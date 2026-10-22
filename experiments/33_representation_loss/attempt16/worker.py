"""Evaluate immutable checkpoints over fixed full histories; no optimizer/training."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from worker_base import *
from original_cnn import decode
from matched_losses import objective_for

def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
 plan=json.loads((R/'coverage-plan.json').read_text());cs=json.loads((R/'cases.json').read_text());assert sorted(c['case'] for c in cs)==plan['cases'] and all(c['split']!='test' for c in cs)
 geoms=dict(np.load(R/'data/geometries.npz'));arrays={c['case']:load(c) for c in cs};allrows=[];started=time.monotonic()
 for item in plan['models']:
  path=R/'data/resume'/item['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
  # A separately reserved continuation can provide immutable completed result shards.
  shard=f"eval-{item['arm']}-{item['step']:05}.json";resume=R/'data/evaluated'/shard
  if resume.exists():
   existing=json.loads(resume.read_text());assert existing['checkpoint']==item and existing['cases']==plan['cases'];allrows+=existing['rows'];continue
  m=GeometryCNN().cuda();state=torch.load(path,map_location='cuda',weights_only=False);m.load_state_dict(state['model']);del state;m.eval();rows=[]
  with torch.no_grad():
   for c in cs:
    a,t=arrays[c['case']];pp=[];loss_sum=0.;ambient=torch.tensor(np.array(a[0,5]),device='cuda');tic=time.monotonic()
    for k in range(0,len(t),3):
     p=predict(m,'current',c,t[k:k+3],geoms[c['case']],'cuda');y=torch.tensor(encode(a[k:k+3],c['wind_speed']),device='cuda');loss=objective_for(item['loss_arm'],p,y,ambient);assert torch.isfinite(loss);loss_sum+=float(loss)*len(p);pp.append(p.cpu().numpy())
    b=decode(np.concatenate(pp),c['wind_speed']);rows.append(dict(arm=item['arm'],step=item['step'],case=c['case'],configuration=c['configuration'],replica=c['replica'],split=c['split'],fixed_history_objective=loss_sum/len(t),prediction_and_objective_s=time.monotonic()-tic,**metrics(np.array(a),b,t)))
  raw=json.dumps(dict(checkpoint=item,cases=plan['cases'],rows=rows)).encode();upload(shard,raw);allrows+=rows;print('EVALUATED',item['arm'],item['step'],len(rows),'elapsed',time.monotonic()-started,flush=True);del m;torch.cuda.empty_cache()
 raw=json.dumps(dict(rows=allrows,plan=plan,scope=plan['scope'],elapsed_s=time.monotonic()-started,input_hashes=json.loads((R/'hashes.json').read_text())),indent=2).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
