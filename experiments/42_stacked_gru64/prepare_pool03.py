"""Verified epoch30 continuation in a new three-region pool; no local optimization."""
from pathlib import Path
import shutil,json,hashlib,subprocess,sys,torch
R=Path(__file__).resolve().parent;D=R/'data/training03';O=R/'results03'
assert json.loads((R/'results02/pool-closed.json').read_text())['passed']
a=json.loads((R/'results02/preemption-audit.json').read_text());assert a['passed'] and a['latest_epoch']==30
assert not (O/'submission-intent.json').exists();O.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
for n in ['worker.py','model.py','plain_model.py','gated_model.py','objective.py','runtime.py','coverage-plan.json','schema.json','data/sequences.npz']:
 dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'data/training02'/n,dest);assert dest.read_bytes()==(R/'data/training02'/n).read_bytes()
resume=D/'data/resume';(resume/'archive').mkdir(parents=True,exist_ok=True)
for n,entry in a['objects'].items():
 name=Path(n).name
 if n.startswith('ia/') and (name.startswith('fold00-epoch') or name in ['fold00-baseline.json','fold00-checkpoint-replay.json']):
  src=R/'data/preempted02'/n;assert hashlib.sha256(src.read_bytes()).hexdigest()==entry['sha256'];shutil.copy2(src,resume/'archive'/name)
shutil.copy2(R/'data/preempted02'/a['checkpoint'],resume/'fold00.pt');assert hashlib.sha256((resume/'fold00.pt').read_bytes()).hexdigest()==a['checkpoint_sha256']
ck=torch.load(resume/'fold00.pt',map_location='cpu',weights_only=False);assert ck['epoch']==30 and ck['optimizer']['state'] and ck['rng']
assert len([v for v in ck['history'] if v['epoch']>0])==30
subprocess.run([sys.executable,str(R/'build_pool03.py')],check=True)
(O/'continuation-validation.json').write_text(json.dumps(dict(passed=True,resume_epoch=30,next_epoch=31,full_optimizer_rng_history=True,checkpoint_sha256=a['checkpoint_sha256'],recipe_byte_identical=True,local_optimizer_executed=False),indent=2)+'\n')
