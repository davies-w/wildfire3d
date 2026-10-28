"""Freeze the complete joint trial package; no cloud actions or fitting."""
from pathlib import Path
import base64,hashlib,io,json,shutil,tarfile,yaml
R=Path(__file__).resolve().parents[1];C=R/'data/joint-decoder-candidate';F=R/'data/joint-rolling-features';D=R/'data/joint-decoder-pilot02';PREFIX='density36/joint-decoder-pilot02/';LABEL='gpu36-joint02'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 assert not (R/'results/joint-decoder-pilot02-execution.json').exists(),'Immutable existing submission; never rebuild'
 p=json.loads((R/'results/joint-decoder-trial02-plan.json').read_text());assert p['status']=='protocol_prepared_not_launched';proof=json.loads((R/'results/joint-pipeline-v2-preflight.json').read_text());assert proof['passed']
 for name,h in proof['source_hashes'].items():assert sha(R/'model_evaluation'/name)==h
 for name,h in p['source_hashes'].items():assert sha(R/'model_evaluation'/name)==h
 assert sha(C/'initial-decoder.pt')==p['initial_decoder_sha256'];assert sha(R/'results/joint-rolling-features-prepared.json')==p['rolling_manifest_sha256']
 for folder,record in [(C,'joint-decoder-candidate-prepared.json'),(F,'joint-rolling-features-prepared.json')]:
  for name,info in json.loads((R/'results'/record).read_text())['files'].items():assert sha(folder/name)==info['sha256']
 D.mkdir(exist_ok=True)
 for name in ['features.npz','base-normalization.json','candidate-plan.json','initial-decoder.pt']:shutil.copyfile(C/name,D/name)
 for src,dst in [('features.npy','rolling-features.npy'),('base-states.npy','rolling-base-states.npy'),('rolling-plan.json','rolling-plan.json')]:shutil.copyfile(F/src,D/dst)
 for src,dst in [('joint_worker.py','worker.py'),('joint_decoder_v2.py','joint_decoder.py'),('joint_decoder_v2.py','joint_decoder_v2.py'),('joint_data.py','joint_data.py'),('joint_metrics.py','joint_metrics.py'),('joint_objective_v2.py','joint_objective.py'),('gas_head_metrics.py','gas_head_metrics.py')]:shutil.copyfile(R/'model_evaluation'/src,D/dst)
 (D/'trial-plan.json').write_text(json.dumps(p,indent=2)+'\n');runtime=(R/'data/gas-shape-pilot01/runtime.py').read_text().replace('density36/gas-shape-pilot01/',PREFIX);assert PREFIX in runtime;(D/'runtime.py').write_text(runtime)
 names=['features.npz','base-normalization.json','candidate-plan.json','initial-decoder.pt','rolling-features.npy','rolling-base-states.npy','rolling-plan.json','worker.py','joint_decoder_v2.py','joint_decoder.py','joint_data.py','joint_metrics.py','joint_objective.py','gas_head_metrics.py','trial-plan.json','runtime.py'];hashes={name:sha(D/name) for name in names}
 for name in names:
  if name.endswith('.py'):compile((D/name).read_text(),name,'exec')
 with tarfile.open(D/'inputs.tar','w') as tar:
  for name in names:
   info=tarfile.TarInfo(name);info.size=(D/name).stat().st_size
   with (D/name).open('rb') as stream:tar.addfile(info,stream)
  payload=json.dumps(hashes,sort_keys=True).encode();info=tarfile.TarInfo('hashes.json');info.size=len(payload);tar.addfile(info,io.BytesIO(payload))
 bootstrap=(R/'data/gas-shape-pilot01/bootstrap.py').read_text().replace('density36/gas-shape-pilot01/',PREFIX);(D/'bootstrap.py').write_text(bootstrap)
 text=(R/'data/gas-shape-pilot01/workflow.yaml').read_text().replace('gpu36-gasshape01',LABEL).replace('density36/gas-shape-pilot01/',PREFIX).replace('+ 3600','+ 2700').replace('+ 1500','+ 810');w=yaml.safe_load(text);task=w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec'];task['maxRunDuration']='690s';task['maxRetryCount']=0;task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"];text=yaml.safe_dump(w,sort_keys=False);assert '+ 2700' in text and '+ 810' in text and 'gasshape01' not in text;(D/'workflow.yaml').write_text(text)
 result=dict(prepared=True,submitted=False,input_sha256=sha(D/'inputs.tar'),input_bytes=(D/'inputs.tar').stat().st_size,workflow_sha256=sha(D/'workflow.yaml'),files=hashes,maximum_allowance_usd=p['budget_plan']['maximum_allowance_usd'],prefix=PREFIX,label=LABEL,epochs_per_arm=300,test_evaluated=False,confirmation_closed_before_freeze=True);assert result['input_bytes']<1024**3;(R/'results/joint-decoder-pilot02-prepared.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
