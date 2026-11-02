"""Build a verified checkpoint116 continuation; no local optimizer or training."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,torch,ast
R=Path(__file__).resolve().parent;D=R/'data/training02';O=R/'results02'
assert not (O/'submission-intent.json').exists();O.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
assert json.loads((R/'results/pool-closed.json').read_text())['passed']
a=json.loads((R/'results/failure-archive.json').read_text());assert a['passed'] and a['completed_epoch']==116
for name in ['model.py','gated_model.py','objective.py','joint_objective.py','runtime.py','coverage-plan.json','schema.json','data/sequences.npz','data/cones.npz']:
 f=D/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'data/training'/name,f)
shutil.copy2(R/'worker02.py',D/'worker.py')
resume=D/'data/resume';(resume/'archive').mkdir(parents=True,exist_ok=True)
for f in (R/'data/interrupted-training').iterdir():
 key='ia/'+f.name;assert hashlib.sha256(f.read_bytes()).hexdigest()==a['objects'][key]['sha256']
 shutil.copy2(f,resume/'archive'/f.name)
shutil.copy2(resume/'archive/fold00-epoch116.pt',resume/'fold00.pt')
ck=torch.load(resume/'fold00.pt',map_location='cpu',weights_only=False)
assert ck['epoch']==116 and ck['optimizer']['state'] and ck['rng'] and ck['best_state']
assert [x['epoch'] for x in ck['history'] if x['epoch']>0]==list(range(1,117))
assert ck['schema_hash']==hashlib.sha256((D/'schema.json').read_bytes()).hexdigest()
sys.dont_write_bytecode=True;sys.path.insert(0,str(D));from model import Transition
m=Transition('gated');m.load_state_dict(ck['model'],strict=True);assert sum(x.numel() for x in m.parameters())==34765
plan=json.loads((D/'coverage-plan.json').read_text());assert next(x['steps'] for x in reversed(plan['horizon_curriculum']) if 117>=x['first_epoch'])==64
assert plan['minimum_epochs']==160 and plan['epochs_max']==400 and plan['patience_epochs']==30
for n in ['worker02.py','cloud_check02.py','build_pool02.py','launch02.py','deploy02.py']:ast.parse((R/n).read_text())
subprocess.run([sys.executable,str(R/'build_pool02.py')],check=True)
(O/'continuation-validation.json').write_text(json.dumps(dict(passed=True,resume_epoch=116,next_epoch=117,horizon=64,parameters=34765,model_strict_load=True,nonempty_optimizer_rng_history=True,best_epoch=ck['best_epoch'],globalstep=ck['globalstep'],checkpoint_sha256=hashlib.sha256((resume/'fold00.pt').read_bytes()).hexdigest(),local_optimizer_executed=False),indent=2)+'\n')
print('Verified checkpoint116 model/optimizer/RNG/history; next epoch117; no local training')
