"""Diagnosed Spot-preemption continuation; no architecture or optimization change."""
from pathlib import Path
import json,hashlib,shutil,tarfile,base64,yaml
R=Path(__file__).resolve().parent;O=R/'results02';D=R/'data/training02';O.mkdir(exist_ok=True)
assert not (O/'submission-intent.json').exists()
a=json.loads((R/'results01/preemption-audit.json').read_text());assert a['passed'] and a['latest_epoch']==27
D.mkdir(exist_ok=True)
for n in ['worker.py','model.py','plain_model.py','gated_model.py','objective.py','runtime.py','coverage-plan.json','schema.json','data/sequences.npz']:
 (D/n).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'data/training01'/n,D/n)
resume=D/'data/resume';(resume/'archive').mkdir(parents=True,exist_ok=True)
for n,v in a['objects'].items():
 if n.startswith('fold00-epoch') or n in ['fold00-baseline.json','fold00-checkpoint-replay.json']:
  src=R/'data/preempted01'/n;assert hashlib.sha256(src.read_bytes()).hexdigest()==v['sha256'];shutil.copy2(src,resume/'archive'/n)
shutil.copy2(R/'data/preempted01'/a['checkpoint'],resume/'fold00.pt')
p=D/'worker.py';s=p.read_text();marker='reports=[]\n';assert s.count(marker)==1
s=s.replace(marker,"""# Preserve original completed epochs in the continuation manifest, byte-for-byte.
for prior in sorted((R/'data/resume/archive').glob('*')):
 data=prior.read_bytes();(folder/prior.name).write_bytes(data);upload(prior.name,data);manifest[prior.name]=hashlib.sha256(data).hexdigest()
reports=[]
""");p.write_text(s)
p=D/'runtime.py';p.write_text(p.read_text().replace('history38/training01/','history38/training02/'))
p=D/'coverage-plan.json';plan=json.loads(p.read_text());plan['budget'].update(soft_seconds=82800,maximum_allowance_usd=18.45);p.write_text(json.dumps(plan,indent=2)+'\n')
shutil.copy2(R/'cloud_check02.py',D/'cloud_check.py')
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.name!='hashes.json' and p.suffix in ('.py','.json','.npz','.pt')}
(D/'hashes.json').write_text(json.dumps(files,indent=2)+'\n')
with tarfile.open(D/'inputs.tar','w') as tar:
 for n in sorted([*files,'hashes.json']):tar.add(D/n,arcname=n)
digest=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest();old=json.loads((R/'results01/package.json').read_text())
boot=(R/'data/training01/bootstrap.py').read_text().replace('history38/training01/','history38/training02/').replace(old['input_sha256'],digest);(D/'bootstrap.py').write_text(boot)
w=yaml.safe_load((R/'data/training01/workflow.yaml').read_text().replace('gpu38-history01','gpu38-history02').replace('history38/training01/','history38/training02/').replace('88200','84600'))
job=w['main']['steps'][0]['initialize']['assign'][0]['job'];job['taskGroups'][0]['taskSpec']['maxRunDuration']='83700s'
job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
(D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
proof=dict(files=files,input_sha256=digest,input_bytes=(D/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),maximum_allowance_usd=18.45,soft_seconds=82800,task_seconds=83700,vm_seconds=84600,allocation_deadline=None,rotation=0,split_counts=old['split_counts'],resume_epoch=27,resume_sha256=files['data/resume/fold00.pt'],prior_manifest_preserved=True)
(O/'package.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'}))
