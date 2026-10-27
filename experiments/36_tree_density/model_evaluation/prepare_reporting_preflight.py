"""Prepare distinct GPU equivalence/timing job for diagnosed reporting overhead."""
from pathlib import Path
import base64,hashlib,io,json,shutil,subprocess,sys,tarfile,yaml
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-fast-reporting-check.json').read_text())['passed']
 old=R/'data/model-preflight';dest=R/'data/model-preflight02';(dest/'data').mkdir(parents=True,exist_ok=True);(dest/'results').mkdir(exist_ok=True)
 files=json.loads((R/'results/model-preflight-inputs.json').read_text())['files']
 for name in files:shutil.copyfile(old/name,dest/name)
 shutil.copyfile(R/'data/model-report-candidate/worker.py',dest/'worker.py');shutil.copyfile(R/'data/model-runner/worker.py',dest/'original_worker.py')
 (dest/'runtime.py').write_text((old/'runtime.py').read_text().replace('model-preflight01/','model-preflight02/'))
 comparison="""# Compare original and optimized reporting on TRAIN only, no fitting.
original_source=(R/'original_worker.py').read_text().split('checks=[]')[0]
original={'__file__':str(R/'worker.py')};exec(compile(original_source,'original-reporting','exec'),original)
old_result=original['evaluate'](model,z,train,mean,std,True)
new_result=ns['evaluate'](model,z,train,mean,std,True)
repeat_result=ns['evaluate'](model,z,train,mean,std,True)
assert new_result==repeat_result,'GPU reporting replay differs'
import math
errors=[]
def compare(a,b):
 if isinstance(a,dict):
  assert a.keys()==b.keys()
  for k in a:compare(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):compare(x,y)
 elif isinstance(a,float):
  assert math.isclose(a,b,rel_tol=1e-5,abs_tol=1e-7),(a,b)
  errors.append(abs(a-b))
 else:assert a==b
compare(old_result,new_result)
ns['save']('report-equivalence.json',{'passed':True,'training':False,'test_evaluation':False,'train_histories':len(train),'deterministic_replay':True,'rtol':1e-5,'atol':1e-7,'max_absolute_difference':max(errors),'scope':'Same configuration weighting, different floating-point reduction order; model/training loss unchanged.'})
"""
 timing=(old/'time_cloud.py').read_text();assert timing.count('measurements=[]')==1
 (dest/'time_cloud.py').write_text(timing.replace('measurements=[]',comparison+'\nmeasurements=[]'))
 for name in ('validate.py','validate_evaluation.py','validate_transport.py'):subprocess.run([sys.executable,str(dest/name)],check=True)
 names=sorted(set(files)|{'original_worker.py'});hashes={n:hashlib.sha256((dest/n).read_bytes()).hexdigest() for n in names}
 out=R/'data/model-timing02';out.mkdir(exist_ok=True)
 with tarfile.open(out/'inputs.tar','w') as tar:
  for name in names:
   data=(dest/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
  data=json.dumps(hashes,sort_keys=True).encode();info=tarfile.TarInfo('hashes.json');info.size=len(data);tar.addfile(info,io.BytesIO(data))
 bootstrap=(R/'data/model-timing/bootstrap.py').read_text().replace('model-preflight01/','model-preflight02/')
 w=yaml.safe_load((R/'data/model-timing/workflow.yaml').read_text());w=json.loads(json.dumps(w).replace('gpu36-preflight01','gpu36-preflight02').replace('model-preflight01/','model-preflight02/'))
 w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 (out/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(out/'bootstrap.py').write_text(bootstrap)
 report=json.loads((R/'results/model-timing-prepared.json').read_text());report.update(workflow_id='fds-gpu36-preflight02',private_prefix='density36/model-preflight02/',input_sha256=hashlib.sha256((out/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(out/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((out/'workflow.yaml').read_bytes()).hexdigest(),funding='Carve .50 from remaining7.50 model reservation',scope='GPU reporting equivalence and timing only; no optimizer/test evaluation')
 (R/'results/model-timing02-prepared.json').write_text(json.dumps(report,indent=2)+'\n');(R/'results/model-preflight02-inputs.json').write_text(json.dumps({'files':hashes,'submitted':False},indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
