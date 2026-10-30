"""Frozen rotation3 repeat: same model/objective/recipe, new split and private prefix."""
from pathlib import Path
import shutil,json,hashlib,tarfile,base64,yaml
R=Path(__file__).resolve().parent;D=R/'data/training06';OUT=R/'results06';OUT.mkdir(exist_ok=True)
assert not (OUT/'submission-intent.json').exists(),'Do not modify submitted inputs'
for n in ['worker.py','model.py','plain_model.py','gated_model.py','objective.py','runtime.py','coverage-plan.json','data/sequences.npz']:
 (D/n).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'data/training03'/n,D/n)
p=D/'runtime.py';p.write_text(p.read_text().replace('integral37/training03/','integral37/training06/'))
p=D/'worker.py';p.write_text(p.read_text().replace('unchanged rotation0 train8/val1/test1 split','frozen rotation3 train8/val1/test1 split'))
p=D/'coverage-plan.json';p.write_text(p.read_text().replace('rotation0','rotation3').replace('57600','86400'))
meta=json.loads((R/'data/training03/schema.json').read_text());full=json.loads((R.parent/'36_tree_density/data/model-training/schema.json').read_text());meta['rotations']=[full['rotations'][3]]
(D/'schema.json').write_text(json.dumps(meta,indent=2)+'\n')
shutil.copy2(R/'cloud_check06.py',D/'cloud_check.py')
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.npz') and p.name!='hashes.json'}
(D/'hashes.json').write_text(json.dumps(files,indent=2))
with tarfile.open(D/'inputs.tar','w') as tar:
 for n in sorted([*files,'hashes.json']):tar.add(D/n,arcname=n)
digest=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()
oldhash=json.loads((R/'results03/package.json').read_text())['input_sha256']
boot=(R/'data/training03/bootstrap.py').read_text().replace('integral37/training03/','integral37/training06/').replace(oldhash,digest);assert digest in boot
(D/'bootstrap.py').write_text(boot)
w=yaml.safe_load((R/'data/training03/workflow.yaml').read_text().replace('gpu37-integral03','gpu37-integral06').replace('integral37/training03/','integral37/training06/'))
steps=w['main']['steps'];assign=steps[0]['initialize']['assign'];assign[:]=[v for v in assign if not ('deadline' in v or 'queue_deadline' in v)]
job=next(v['job'] for v in assign if 'job' in v)
job['taskGroups'][0]['taskSpec']['maxRunDuration']='87300s'
policy=job['allocationPolicy']['instances'][0]['policy'];policy['provisioningModel']='SPOT';policy['machineType']='n1-standard-4';policy['accelerators']=[dict(type='nvidia-tesla-t4',count=1)]
job['allocationPolicy']['location']['allowedLocations']=['zones/us-west4-a','zones/us-west4-b']
job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
monitor=next(s['monitor'] for s in steps if 'monitor' in s)['try']['steps'];checks=next(s['check'] for s in monitor if 'check' in s)['switch'];checks[:]=[x for x in checks if 'deadline' not in x['condition']]
next(s['wait'] for s in monitor if 'wait' in s)['args']['seconds']='${if(len(default(map.get(active_vms.body, "items"), [])) == 0, 300, 30)}'
txt=yaml.safe_dump(w,sort_keys=False).replace('us-west4-c','us-west4-b').replace('59400','88200');assert 'queue_deadline' not in txt and 'sys.now() >= deadline' not in txt and '+ 88200' in txt
txt=txt.replace('us-west4','us-west1').replace('fds-timing-west4','fds-timing-west1')
(D/'workflow.yaml').write_text(txt)
proof=dict(files=files,input_sha256=digest,input_bytes=(D/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),maximum_allowance_usd=19.2,soft_seconds=86400,task_seconds=87300,vm_seconds=88200,allocation_deadline=None,rotation=3,split_counts={k:len(meta['rotations'][0][k]) for k in ['train','validation','test']})
(OUT/'package.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'}))
