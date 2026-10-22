"""Infrastructure benchmark, not scientific retraining. Coarsened real training targets."""
import json,time,os,io,base64,zlib,urllib.request,urllib.parse,traceback
from pathlib import Path
import numpy as np
import torch
from models import Model
from original_cnn import cond,encode
from previous_loss import objective
R=Path(__file__).parent
BUCKET='tmrw-wildfire-20261015-trial'
def upload(name,data):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 token=json.load(urllib.request.urlopen(req,timeout=15))['access_token']
 url='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote('gpu29/test03/'+name,safe='')
 req=urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST')
 urllib.request.urlopen(req,timeout=60).read()
def main():
 assert torch.cuda.is_available(),'CUDA unavailable'
 torch.set_num_threads(4);torch.manual_seed(2903)
 torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
 torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 meta=json.loads((R/'sample.json').read_text());a=np.load(R/'sample.npy').astype('float32')
 # Expand sampled targets back to original output shape. No claimed accuracy assessment.
 y=torch.from_numpy(encode(a,meta['wind_speed'])).cuda();y=torch.nn.functional.interpolate(y,size=(48,32,32),mode='nearest')
 c=torch.from_numpy(cond(meta,np.array(meta['times']))).cuda()
 m=Model('heads',6).cuda()
 for p in m.strength.parameters():p.requires_grad_(False)
 opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=.0001,weight_decay=1e-5)
 def step():
  opt.zero_grad();loss=objective(m(c),y);assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step();return float(loss.detach())
 for _ in range(5):step()
 torch.cuda.synchronize();start=time.perf_counter();losses=[]
 for i in range(100):
  losses.append(step())
  if (i+1)%25==0:
   b=io.BytesIO();torch.save({'model':m.state_dict(),'optimizer':opt.state_dict(),'step':i+1,'rng_cpu':torch.get_rng_state(),'rng_cuda':torch.cuda.get_rng_state_all()},b);upload('checkpoint-%03d.pt'%(i+1),b.getvalue())
 torch.cuda.synchronize();elapsed=time.perf_counter()-start
 checkpoint=b.getvalue();expected_loss=step();expected={k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
 saved=torch.load(io.BytesIO(checkpoint),map_location='cuda',weights_only=False);m.load_state_dict(saved['model']);opt.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['rng_cpu'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in saved['rng_cuda']]);resumed_loss=step()
 difference=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in m.state_dict().items());assert difference<1e-5,(difference,expected_loss,resumed_loss)
 cc=torch.from_numpy(cond(meta,np.arange(0,181,2,dtype=float))).cuda();timings=[]
 with torch.no_grad():
  for _ in range(4):
   torch.cuda.synchronize();start=time.perf_counter()
   for k in range(0,91,2): out=m(cc[k:k+2]);assert torch.isfinite(out).all()
   torch.cuda.synchronize();timings.append(time.perf_counter()-start)
 result=dict(gpu=torch.cuda.get_device_name(),torch=torch.__version__,cuda=torch.version.cuda,training_steps=100,training_seconds_including_four_checkpoint_uploads=elapsed,seconds_per_step_including_checkpoints=elapsed/100,inference_91_frames_seconds=timings,inference_median_s=float(np.median(timings[1:])),peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),checkpoint_resume_max_weight_difference=difference,loss_first=losses[0],loss_last=losses[-1],target_note='Two training frames spatially subsampled by 4 then nearest-upsampled to full output dimensions; fresh model weights; hardware/recovery test only. No validation/test data. Not a fitted scientific model.')
 upload('result.json',json.dumps(result,indent=2).encode());print(json.dumps(result),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException:
  error=traceback.format_exc();print(error,flush=True)
  try:upload('error.txt',error.encode())
  except Exception:pass
  raise
