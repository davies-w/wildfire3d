"""Freeze distinct cloud timing package and guarded submission helpers."""
from pathlib import Path
import json,hashlib,io,tarfile,base64,shutil,yaml
R=Path(__file__).resolve().parents[1];D=R/'data/model-pair';T=R/'data/model-pair-timing'
def main():
 assert json.loads((R/'results/model-pair-validation.json').read_text())['passed']
 assert (D/'time_cloud.py').read_bytes()==(R/'model_evaluation/time_pair.py').read_bytes();T.mkdir(exist_ok=True)
 names=['worker.py','model.py','plain_model.py','gated_model.py','runtime.py','schema.json','coverage-plan.json','data/sequences.npz','time_cloud.py'];hashes={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names}
 with tarfile.open(T/'inputs.tar','w') as tar:
  for n in names:
   b=(D/n).read_bytes();i=tarfile.TarInfo(n);i.size=len(b);tar.addfile(i,io.BytesIO(b))
  b=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(b);tar.addfile(i,io.BytesIO(b))
 bootstrap=(R/'data/model-timing03/bootstrap.py').read_text().replace('model-preflight03/','model-pair-preflight01/')
 w=json.loads(json.dumps(yaml.safe_load((R/'data/model-timing03/workflow.yaml').read_text())).replace('gpu36-preflight03','gpu36-paircheck01').replace('model-preflight03/','model-pair-preflight01/'))
 w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 (T/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(T/'bootstrap.py').write_text(bootstrap)
 report=dict(submitted=False,input_sha256=hashlib.sha256((T/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(T/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((T/'workflow.yaml').read_bytes()).hexdigest(),files=hashes,maximum_allowance_usd=.5,task_seconds=900,vm_age_seconds=1200,absolute_seconds=2700,queue_seconds=1200)
 (R/'results/model-pair-timing-prepared.json').write_text(json.dumps(report,indent=2)+'\n')
 for src,dest in [('launch_timing03.py','launch_pair_timing.py'),('collect_timing03.py','collect_pair_timing.py'),('close_timing03.py','close_pair_timing.py')]:
  s=(R/'model_evaluation'/src).read_text().replace('model-timing03','model-pair-timing').replace('model-preflight03','model-pair-preflight01').replace('gpu36-preflight03','gpu36-paircheck01')
  if src.startswith('launch'):
   s=s.replace("  for name in ('preflight','evaluation-preflight','transport-preflight'):assert read('data/model-pair-preflight01/results/'+name+'.json')['passed']","  assert read('results/model-pair-validation.json')['passed']")
   begin=s.index("   source=b['reservations']['density36-learning']");end=s.index("   B.write_text",begin)
   s=s[:begin]+"   assert b['estimated_spend_usd']+b['reserved_usd']+.5<=b['authorized_usd']\n   b['reserved_usd']+=.5\n   b['reservations'][KEY]=dict(state='reserved_before_upload',allowance_usd=.5,reserved_unix=time.time(),scope='Authorized matched pair CUDA full-epoch timing;20min VM bound')\n"+s[end:]
  if src.startswith('collect'):s=s.replace("'report-equivalence.json',",'')
  compile(s,dest,'exec');(R/'model_evaluation'/dest).write_text(s)
 print(json.dumps(report))
if __name__=='__main__':main()
