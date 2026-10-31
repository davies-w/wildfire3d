"""CPU forward-only initialization/dropout/transport audit. No local optimizer."""
from pathlib import Path
import ast,json,hashlib,importlib.util,torch,yaml
R=Path(__file__).resolve().parent;D=R/'data/training'
spec=importlib.util.spec_from_file_location('fresh_gated',D/'gated_model.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
torch.manual_seed(3516);m=mod.Transition('gated');assert sum(p.numel() for p in m.parameters())==25159
assert isinstance(m.shared[-1],torch.nn.Dropout) and m.shared[-1].p==.1
assert torch.count_nonzero(m.head.weight)==0 and torch.count_nonzero(m.head.bias)==0
assert torch.all(m.gate_head.bias==4) and torch.count_nonzero(m.gate_head.weight)==0
with torch.no_grad():
 x=torch.randn(16,64);m.eval();assert torch.equal(m.shared(x),m.shared(x))
 m.train();rng=torch.get_rng_state();a=m.shared(x);assert not torch.equal(a,m.shared(x));torch.set_rng_state(rng);assert torch.equal(a,m.shared(x))
p=json.loads((D/'coverage-plan.json').read_text());assert 'continuation' not in p and p['minimum_epochs']==160 and p['dropout_probability']==.1
assert p['horizon_curriculum']==[dict(first_epoch=e,steps=h) for e,h in [(1,1),(21,8),(41,16),(61,32),(110,64),(130,90)]]
assert not (D/'data/resume').exists()
schema=json.loads((D/'schema.json').read_text());rot=schema['rotations'][0];assert rot['rotation']==0 and [len(rot[k]) for k in ['train','validation','test']]==[1662,210,208]
assert len({tuple(schema['cases'][i]['physical_key']) for i in rot['test']})==204
for n,h in json.loads((D/'hashes.json').read_text()).items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
for f in [*R.glob('*.py'),*D.glob('*.py')]:ast.parse(f.read_text())
cs=yaml.safe_load((R/'pool01.yaml').read_text())['main']['steps'][0]['initialize']['assign'][0]['candidates'];assert len(cs)==3
for c in cs:
 q=c['job']['allocationPolicy']['instances'][0]['policy'];t=c['job']['taskGroups'][0]['taskSpec'];assert q['provisioningModel']=='SPOT' and q['machineType']=='n1-standard-4' and q['accelerators']==[dict(type='nvidia-tesla-t4',count=1)] and t['maxRetryCount']==0
assert 'mm.eval();mm.load_state_dict' in (D/'worker.py').read_text()
proof=dict(passed=True,parameters=25159,dropout=.1,fresh_initialization=True,no_resume_artifacts=True,eval_deterministic=True,shared_train_stochastic=True,restored_rng_forward_bitwise=True,optimizer_executed=False,cloud_backward_still_required=True)
(R/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
