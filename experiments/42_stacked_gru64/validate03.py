"""Verify continuation transport and full state on CPU, without optimizer execution."""
from pathlib import Path
import ast,json,hashlib,torch,importlib.util,yaml
R=Path(__file__).resolve().parent;D=R/'data/training03';a=json.loads((R/'results02/preemption-audit.json').read_text());p=json.loads((R/'results03/package.json').read_text())
for n,h in p['files'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
for n in ['worker.py','model.py','plain_model.py','gated_model.py','objective.py','runtime.py','coverage-plan.json','schema.json','data/sequences.npz']:assert (D/n).read_bytes()==(R/'data/training02'/n).read_bytes()
ck=torch.load(D/'data/resume/fold00.pt',map_location='cpu',weights_only=False);assert ck['epoch']==30 and ck['optimizer']['state'] and ck['rng'] and ck['globalstep']>0
assert [v['epoch'] for v in ck['history'] if v['epoch']>0]==list(range(1,31));assert 1<=ck['best_epoch']<=30
assert hashlib.sha256((D/'data/resume/fold00.pt').read_bytes()).hexdigest()==a['checkpoint_sha256']==p['resume_sha256']
spec=importlib.util.spec_from_file_location('continued',D/'gated_model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);model=m.Transition('gated');model.load_state_dict(ck['model'],strict=True);assert sum(v.numel() for v in model.parameters())==50119
for epoch in range(1,31):
 for ext in ['pt','json']:
  n=f'fold00-epoch{epoch:03}.{ext}';assert hashlib.sha256((D/'data/resume/archive'/n).read_bytes()).hexdigest()==a['objects']['ia/'+n]['sha256']
plan=json.loads((D/'coverage-plan.json').read_text());assert next(x['steps'] for x in reversed(plan['horizon_curriculum']) if 31>=x['first_epoch'])==8
for f in [*R.glob('*.py'),*D.glob('*.py')]:ast.parse(f.read_text())
assert 'epoch=31,horizon=8' in (D/'cloud_check.py').read_text()
cs=yaml.safe_load((R/'pool03.yaml').read_text())['main']['steps'][0]['initialize']['assign'][0]['candidates'];assert len(cs)==3
for c in cs:
 q=c['job']['allocationPolicy']['instances'][0]['policy'];assert q['provisioningModel']=='SPOT' and q['accelerators']==[dict(type='nvidia-tesla-t4',count=1)]
proof=dict(passed=True,epoch=30,next_epoch=31,horizon=8,parameters=50119,checkpoint_sha256=a['checkpoint_sha256'],model_optimizer_rng_history_verified=True,all_prior_epochs_byte_identical=True,recipe_byte_identical=True,local_optimizer_executed=False,cloud_exact_next_update_replay_required=True)
(R/'validation03.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
