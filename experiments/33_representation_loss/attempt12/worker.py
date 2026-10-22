"""Frozen broader-development evaluation; no optimizer or model selection."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from worker_base import *
from original_cnn import decode

def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
 cs=json.loads((R/'cases.json').read_text());plan=json.loads((R/'evaluation-plan.json').read_text());assert all(c['split']!='test' for c in cs);assert sorted(c['case'] for c in cs)==plan['cases']
 for n,h in plan['models'].items():assert hashlib.sha256((R/'data/resume'/n).read_bytes()).hexdigest()==h
 geoms=dict(np.load(R/'data/geometries.npz'));rows=[];histories=[];projections={};started=time.monotonic()
 for arm in ['current','control','dose_background','physical_low']:
  m=GeometryCNN().cuda();saved=torch.load(R/'data/resume'/f'{arm}.pt',map_location='cuda',weights_only=False);m.load_state_dict(saved['model']);m.eval()
  with torch.no_grad():
   for c in cs:
    a,t=load(c);torch.cuda.synchronize();tic=time.monotonic();pp=[predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda').cpu().numpy() for k in range(0,len(t),3)];torch.cuda.synchronize();elapsed=time.monotonic()-tic
    b=decode(np.concatenate(pp),c['wind_speed']);truth=np.array(a);rows.append(dict(arm=arm,case=c['case'],configuration=c['configuration'],replica=c['replica'],split=c['split'],inference_s=elapsed,**metrics(truth,b,t)))
    histories.append(dict(arm=arm,case=c['case'],time_s=t.tolist(),truth_HRR_kW=(truth[:,1].sum((1,2,3))*.125).tolist(),predicted_HRR_kW=(b[:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=truth[:,0].max((1,2,3)).tolist(),predicted_peak_C=b[:,0].max((1,2,3)).tolist()))
    if c['case'] in plan['animation_cases']:
     projections[c['case']+'_'+arm]=b[:,[0,1]].max(axis=3)
     if arm=='current':projections[c['case']+'_FDS']=truth[:,[0,1]].max(axis=3);projections[c['case']+'_time']=t
  upload(arm+'-results.json',json.dumps(dict(rows=[x for x in rows if x['arm']==arm])).encode());del m;torch.cuda.empty_cache()
 buf=io.BytesIO();np.savez_compressed(buf,**projections);upload('projections.npz',buf.getvalue())
 raw=json.dumps(dict(rows=rows,histories=histories,scope=plan['scope'],elapsed_s=time.monotonic()-started,freeze=plan),indent=2).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
