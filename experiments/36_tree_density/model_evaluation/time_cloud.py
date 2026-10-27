"""Cloud CUDA checks and measured train-only forward/backward timings, no optimizer."""
from pathlib import Path
import json,time
R=Path(__file__).resolve().parent
# Executes the unchanged worker CUDA/backward and complete validation-report checks only.
source=(R/'worker.py').read_text().split('reports=[]')[0]
assert 'optimizer=' not in source and 'optimizer.step' not in source
ns={'__file__':str(R/'worker.py')};exec(compile(source,'worker-preflight','exec'),ns)
torch=ns['torch'];model=ns['Transition']('control').to('cuda');train=torch.tensor(ns['meta']['rotations'][0]['train'],device='cuda')
mean,std=ns['normalize_fit'](ns['raw'],train,ns['config'],ns['scale']);model.set_normalization(mean,std);z=(torch.asinh(ns['raw']/ns['scale'])-mean)/std
# Nonzero head exercises recurrent gradient without fitting any parameters.
with torch.no_grad():model.head.weight.fill_(.001)
measurements=[]
for h in (1,8,16,32):
 for origin in (0,32,64):
  ids=train[:256];js=torch.full_like(ids,origin)
  torch.cuda.synchronize();start=time.monotonic();hist=ns['history_at'](z,ids,js);memory=ns['prefix_memory'](model,z,ids,js);loss=0
  for step in range(h):
   jj=(js+step).clamp_max(89);keep=js+step<90
   state,memory=model.step(hist,ns['external'][ids,jj],memory)
   loss+=(ns['training_objective'](state,z[ids,jj+1])*keep).sum();hist=ns['advance'](hist,state)
  model.zero_grad(set_to_none=True);loss.backward();torch.cuda.synchronize()
  assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters())
  measurements.append({'horizon':h,'origin':origin,'batch':len(ids),'seconds':time.monotonic()-start})
valid=torch.tensor(ns['meta']['rotations'][0]['validation'],device='cuda');torch.cuda.synchronize();start=time.monotonic()
for ids in (train,valid):
 result=ns['evaluate'](model,z,ids,mean,std)
 assert all(result[m]['finite'] for m in ('one_step','rollout'))
torch.cuda.synchronize();evaluation=time.monotonic()-start
ns['save']('timing.json',{'passed':True,'training':False,'optimizer_created':False,'test_evaluated':False,'train_validation_evaluation_seconds':evaluation,'batches':measurements,'limitations':'No optimizer updates. Warmup, GPU load, prefix origin, checkpoint transfer, all-origin forecasts and stopping epochs affect wall time. Use conservative margin and measured deadlines.'})
ns['save']('complete.json',{'passed':True,'training':False,'purpose':'CUDA and timing preflight only'})
