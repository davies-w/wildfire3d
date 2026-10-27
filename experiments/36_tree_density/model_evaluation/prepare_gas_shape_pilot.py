"""Freeze the cloud package for one bounded comparison; never launch."""
from pathlib import Path
import base64,hashlib,io,json,shutil,tarfile,yaml
R=Path(__file__).resolve().parents[1];SOURCE=R/'data/gas-head-candidate';D=R/'data/gas-shape-pilot01';PREFIX='density36/gas-shape-pilot01/';LABEL='gpu36-gasshape01'
def main():
 assert not (R/'results/gas-shape-pilot01-execution.json').exists(),'Existing immutable submission; never rebuild'
 assert json.loads((R/'results/gas-shape-head-preflight.json').read_text())['passed']
 assert json.loads((R/'results/gas-head-candidate-preflight.json').read_text())['passed'];assert json.loads((R/'results/gas-head-metrics-preflight.json').read_text())['passed'];plan=json.loads((R/'results/gas-shape-pilot-plan.json').read_text());assert plan['status']=='prepared_not_launched';D.mkdir(exist_ok=True)
 for name in ['features.npz','initial-head.pt','base-normalization.json','candidate-plan.json','gas_head.py']:shutil.copyfile(SOURCE/name,D/name)
 assert hashlib.sha256((D/'features.npz').read_bytes()).hexdigest()==plan['features_sha256'];assert hashlib.sha256((D/'initial-head.pt').read_bytes()).hexdigest()==plan['initial_head_sha256']
 for src,dst in [('gas_shape_worker.py','worker.py'),('gas_head_metrics.py','gas_head_metrics.py'),('gas_shape_metrics.py','gas_shape_metrics.py'),('gas_shape_head.py','gas_shape_head.py')]:shutil.copyfile(R/'model_evaluation'/src,D/dst)
 (D/'pilot-plan.json').write_text(json.dumps(plan,indent=2)+'\n');runtime=(R/'data/exposure-pilot02/runtime.py').read_text().replace('density36/exposure-pilot02/',PREFIX);assert PREFIX in runtime;(D/'runtime.py').write_text(runtime)
 names=['features.npz','initial-head.pt','base-normalization.json','candidate-plan.json','gas_head.py','worker.py','gas_head_metrics.py','gas_shape_metrics.py','gas_shape_head.py','pilot-plan.json','runtime.py'];hashes={name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in names}
 for name in names:
  if name.endswith('.py'):compile((D/name).read_text(),name,'exec')
 with tarfile.open(D/'inputs.tar','w') as tar:
  for name in names:
   b=(D/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(b);tar.addfile(info,io.BytesIO(b))
  b=json.dumps(hashes,sort_keys=True).encode();info=tarfile.TarInfo('hashes.json');info.size=len(b);tar.addfile(info,io.BytesIO(b))
 bootstrap=(R/'data/exposure-pilot02/bootstrap.py').read_text().replace('density36/exposure-pilot02/',PREFIX);assert PREFIX in bootstrap;(D/'bootstrap.py').write_text(bootstrap)
 raw=(R/'data/exposure-pilot02/workflow.yaml').read_text().replace('gpu36-exposure02',LABEL).replace('density36/exposure-pilot02/',PREFIX).replace('+ 4500','+ 3600').replace('+ 3000','+ 1500');w=yaml.safe_load(raw);assigns=w['main']['steps'][0]['initialize']['assign'];task=assigns[1]['job']['taskGroups'][0]['taskSpec'];task['maxRunDuration']='1350s';task['maxRetryCount']=0;task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"];raw=yaml.safe_dump(w,sort_keys=False);assert '+ 3600' in raw and '+ 1500' in raw and 'exposure02' not in raw and PREFIX in raw;(D/'workflow.yaml').write_text(raw)
 proof=dict(prepared=True,submitted=False,input_sha256=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(D/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),files=hashes,maximum_allowance_usd=.4,prefix=PREFIX,label=LABEL,epochs_per_arm=300,test_evaluated=False)
 (R/'results/gas-shape-pilot01-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
