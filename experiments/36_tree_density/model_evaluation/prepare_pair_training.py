"""Freeze two sequential arms after measured complete-epoch CUDA timing."""
from pathlib import Path
import json,hashlib,io,tarfile,base64,shutil,math,yaml
R=Path(__file__).resolve().parents[1];D=R/'data/model-pair';T=R/'data/model-pair-training'
def main():
 assert json.loads((R/'results/model-pair-timing-collected.json').read_text())['passed']
 rows=json.loads((R/'data/model-pair-timing-results/timing.json').read_text())['measurements'];projections={}
 for epochs in (100,400):
  total=0;arms={}
  for kind in ('control','gated'):
   rates={x['horizon']:x['seconds'] for x in rows if x['kind']==kind and 'horizon' in x};evaluation=next(x['evaluation_seconds'] for x in rows if x['kind']==kind and 'evaluation_seconds' in x)
   measured=sum(rates[1 if e<=20 else 8 if e<=40 else 16 if e<=60 else 32]+evaluation for e in range(1,epochs+1));arms[kind]=measured;total+=measured
  projections[str(epochs)]=dict(measured_seconds=total,conservative_seconds=2*total+2*epochs*2+1800,hours=(2*total+2*epochs*2+1800)/3600,arm_measured_seconds=arms)
 # Round the full400-epoch conservative projection upward to an hour.
 soft=math.ceil(projections['400']['conservative_seconds']/3600)*3600;task=soft+900;vm=soft+1800;absolute=vm+1800;allowance=round(.8*vm/3600+.4,2)
 b=json.loads((R.parent/'33_representation_loss/budget.json').read_text());assert b['estimated_spend_usd']+b['reserved_usd']+allowance<=b['authorized_usd']
 plan=dict(projections=projections,soft_seconds=soft,task_seconds=task,vm_age_seconds=vm,absolute_seconds=absolute,queue_seconds=1200,maximum_allowance_usd=allowance,rate_ceiling_usd_per_hour=.8,margin='2x all measured compute including evaluation;2s per epoch uploads;30min forecasts/startup;900s deadline grace;1800s VM overhead',resume_policy='Every epoch model/optimizer/RNG/history/best preserved; deadline saves checkpoint. No automatic paid continuation; diagnose and budget a new immutable-prefix continuation.',test_policy='Both selections frozen before either test',next_rotation='Only prepare rotation1 pair if this pair completes before2026-10-27T15:00:00Z; separate budget check')
 (R/'results/model-pair-runtime-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 (T/'data').mkdir(parents=True,exist_ok=True)
 shutil.copyfile(R/'model_evaluation/check_pair_resume_cloud.py',T/'check_resume.py')
 names=['check_resume.py','worker.py','model.py','plain_model.py','gated_model.py','runtime.py','schema.json','coverage-plan.json','data/sequences.npz']
 for n in names:
  if n!='check_resume.py':shutil.copyfile(D/n,T/n)
 (T/'runtime.py').write_text((T/'runtime.py').read_text().replace('model-pair-preflight01/','model-pair-training01/'))
 p=json.loads((T/'coverage-plan.json').read_text());p['budget']={'soft_seconds':soft,'maximum_allowance_usd':allowance};(T/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
 hashes={n:hashlib.sha256((T/n).read_bytes()).hexdigest() for n in names}
 with tarfile.open(T/'inputs.tar','w') as tar:
  for n in names:
   b=(T/n).read_bytes();i=tarfile.TarInfo(n);i.size=len(b);tar.addfile(i,io.BytesIO(b))
  b=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(b);tar.addfile(i,io.BytesIO(b))
 bootstrap=(R/'data/model-pair-timing/bootstrap.py').read_text().replace('model-pair-preflight01/','model-pair-training01/').replace("p/'time_cloud.py'","p/'worker.py'")
 bootstrap=bootstrap.replace(" runpy.run_path(str(p/'worker.py'),run_name='__main__')"," runpy.run_path(str(p/'check_resume.py'),run_name='__main__')\n runpy.run_path(str(p/'worker.py'),run_name='__main__')")
 w=json.loads(json.dumps(yaml.safe_load((R/'data/model-pair-timing/workflow.yaml').read_text())).replace('gpu36-paircheck01','gpu36-pairtrain01').replace('model-pair-preflight01/','model-pair-training01/').replace('+ 2700',f'+ {absolute}').replace('900s',f'{task}s'))
 # Only VM creation-age expression changes; allocation queue stays1200s.
 def age(v):
  if isinstance(v,dict):return {k:age(x) for k,x in v.items()}
  if isinstance(v,list):return [age(x) for x in v]
  if isinstance(v,str) and 'creationTimestamp' in v:return v.replace('+ 1200',f'+ {vm}')
  return v
 w=age(w)
 assert any('creationTimestamp' in str(x) and str(vm) in str(x) for x in w['main']['steps'])
 w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 (T/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(T/'bootstrap.py').write_text(bootstrap)
 proof=dict(plan,submitted=False,input_sha256=hashlib.sha256((T/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(T/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((T/'workflow.yaml').read_bytes()).hexdigest(),files=hashes)
 (R/'results/model-pair-training-prepared.json').write_text(json.dumps(proof,indent=2)+'\n')
 s=(R/'model_evaluation/launch_training.py').read_text().replace('model-training','model-pair-training').replace('gpu36-training01','gpu36-pairtrain01').replace('density36-learning','density36-pair-training01')
 s=s.replace("assert read('results/model-timing03-collected.json')['passed']","assert read('results/model-pair-timing-collected.json')['passed']").replace("  assert read('data/model-timing03-results/report-equivalence.json')['passed']\n",'')
 begin=s.index("   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());source=");end=s.index('   B.write_text',begin)
 s=s[:begin]+"   fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());assert KEY not in b['reservations']\n   allowance=p['maximum_allowance_usd'];assert b['estimated_spend_usd']+b['reserved_usd']+allowance<=b['authorized_usd']\n   b['reserved_usd']+=allowance;b['reservations'][KEY]=dict(state='preparing_upload',allowance_usd=allowance,reserved_unix=time.time(),scope='Authorized single rotation0 plain/gated stride-one pair; cloud watchdog; no automatic retries',workflow=WF)\n"+s[end:]
 s=s.replace('datetime.timedelta(hours=12)',f'datetime.timedelta(seconds={absolute+7200})').replace('Frozen private ten-fold training','Private matched single-split pair training')
 compile(s,'launch-pair-training','exec');(R/'model_evaluation/launch_pair_training.py').write_text(s)
 print(json.dumps(plan))
if __name__=='__main__':main()
