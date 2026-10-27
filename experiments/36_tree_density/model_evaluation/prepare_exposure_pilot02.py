"""Freeze controlled continuation inputs and bounded workflow; no cloud operations."""
from pathlib import Path
import json,hashlib,shutil,tarfile,io,yaml,base64
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02';SOURCE=R/'data/pair-sequence/rotation0';PREFIX='density36/exposure-pilot02/';LABEL='gpu36-exposure02'
def main():
 assert json.loads((R/'results/exposure-pilot-zero-allocation-proof.json').read_text())['passed'];assert json.loads((R/'results/exposure-pilot-permission-removed.json').read_text())['exact_grant_removed']
 plan=json.loads((R/'results/exposure-pilot-plan.json').read_text());assert plan['status']=='prepared_not_launched';assert json.loads((R/'results/exposure-candidate-preflight.json').read_text())['passed']
 plan['allocation_recovery']={'prior_execution':'1cb22600-a84f-4e9b-b722-5f3deb9857e1','reason':'Every VM insertion failed for zone capacity; zero task execution','new_zone':'us-central1-a','scientific_comparison_unchanged':True}
 (D/'data').mkdir(parents=True,exist_ok=True)
 head=(R/'data/exposure-candidate/worker.py').read_text().split('\nchecks=[]\n')[0];assert 'def restore_rng' in head and 'for rotation in' not in head
 body=(R/'model_evaluation/exposure_pilot_body.py').read_text();worker=head+'\n'+body;compile(worker,'worker.py','exec');(D/'worker.py').write_text(worker)
 for n in ['model.py','plain_model.py','gated_model.py','schema.json','coverage-plan.json','data/sequences.npz']:shutil.copyfile(SOURCE/n,D/n)
 runtime=(SOURCE/'runtime.py').read_text().replace("PREFIX='density36/pair-sequence01/rotation0/'",f"PREFIX='{PREFIX}'");assert PREFIX in runtime;(D/'runtime.py').write_text(runtime)
 shutil.copyfile(R/plan['initial_checkpoint'],D/'data/initial.pt');assert hashlib.sha256((D/'data/initial.pt').read_bytes()).hexdigest()==plan['initial_checkpoint_sha256'];(D/'pilot-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 names=['worker.py','model.py','plain_model.py','gated_model.py','runtime.py','schema.json','coverage-plan.json','pilot-plan.json','data/sequences.npz','data/initial.pt'];hashes={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names}
 with tarfile.open(D/'inputs.tar','w') as tar:
  for n in names:
   b=(D/n).read_bytes();i=tarfile.TarInfo(n);i.size=len(b);tar.addfile(i,io.BytesIO(b))
  b=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(b);tar.addfile(i,io.BytesIO(b))
 bootstrap=(R/'data/model-pair-training/bootstrap.py').read_text().replace('density36/model-pair-training01/',PREFIX).replace(" runpy.run_path(str(p/'check_resume.py'),run_name='__main__')\n",'');assert 'check_resume.py' not in bootstrap;(D/'bootstrap.py').write_text(bootstrap)
 w=yaml.safe_load((R/'data/model-pair-training/workflow.yaml').read_text());w=json.loads(json.dumps(w).replace('gpu36-pairtrain01',LABEL).replace('density36/model-pair-training01/',PREFIX))
 assigns=w['main']['steps'][0]['initialize']['assign'];assigns[0]['deadline']='${sys.now() + 4500}';job=assigns[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(plan['budget_plan']['task_cap_s'])+'s';task['maxRetryCount']=0;task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 for x in assigns:
  if 'queue_deadline' in x:x['queue_deadline']='${sys.now() + 900}'
 def age(v):
  if isinstance(v,dict):return {k:age(x) for k,x in v.items()}
  if isinstance(v,list):return [age(x) for x in v]
  if isinstance(v,str) and 'creationTimestamp' in v:return v.replace('+ 66600','+ 3000')
  return v
 w=age(w);raw=yaml.safe_dump(w,sort_keys=False).replace('us-central1-c','us-central1-a');assert '+ 3000' in raw and '+ 66600' not in raw and 'pairtrain01' not in raw and PREFIX in raw;(D/'workflow.yaml').write_text(raw)
 proof={'prepared':True,'submitted':False,'input_sha256':hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest(),'input_bytes':(D/'inputs.tar').stat().st_size,'workflow_sha256':hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),'files':hashes,'maximum_allowance_usd':.75,'prefix':PREFIX,'label':LABEL,'same_checkpoint_and_optimizer':True,'epochs_per_arm':12,'test_evaluated':False,'normalization':'Frozen train-only values independently checked before continuation','resume_policy':'Batch cursor/model/optimizer/RNG/history/best in each checkpoint; subsequent diagnosed continuation requires fresh prefix and budget.'};(R/'results/exposure-pilot02-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
