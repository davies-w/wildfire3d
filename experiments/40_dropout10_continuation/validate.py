"""CPU forward-only dropout and checkpoint compatibility checks; no optimizer."""
from pathlib import Path
import ast,hashlib,json,importlib.util
import torch,yaml
R=Path(__file__).resolve().parent;D=R/'data/training'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
new=load(D/'gated_model.py','dropout_model');old=load(R.parent/'39_long_window_continuation/data/training02/gated_model.py','parent_model')
ck=torch.load(D/'data/resume/fold00.pt',map_location='cpu',weights_only=False);assert ck['epoch']==ck['best_epoch']==159 and ck['optimizer']['state'] and ck['rng']
a=new.Transition('gated');b=old.Transition('gated');a.load_state_dict(ck['model'],strict=True);b.load_state_dict(ck['model'],strict=True)
assert sum(p.numel() for p in a.parameters())==25159
assert isinstance(a.shared[2],torch.nn.Dropout) and a.shared[2].p==.1
x=torch.randn(16,8,4);u=torch.randn(16,9);u[:,-1]=1
with torch.no_grad():
 a.eval();b.eval();assert torch.equal(a(x,u),b(x,u));assert torch.equal(a.last_gate_logits,b.last_gate_logits)
 a.train();rng=torch.get_rng_state();first=a(x,u);gates=a.last_gate_logits.clone();second=a(x,u);assert not torch.equal(first,second)
 torch.set_rng_state(rng);assert torch.equal(first,a(x,u)) and torch.equal(gates,a.last_gate_logits)
assert all(torch.equal(v,a.state_dict()[k]) for k,v in ck['model'].items())
p=json.loads((D/'coverage-plan.json').read_text());assert p['minimum_epochs']==190 and p['epochs_max']==400 and p['horizon_curriculum'][-1]=={'first_epoch':160,'steps':90}
assert len(list((D/'data/resume/archive').glob('fold00-epoch*.json')))==159
assert not (D/'data/resume/archive/fold00-epoch160.pt').exists()
for n,h in json.loads((D/'hashes.json').read_text()).items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
for f in R.glob('*.py'):ast.parse(f.read_text())
w=yaml.safe_load((R/'pool01.yaml').read_text());cs=w['main']['steps'][0]['initialize']['assign'][0]['candidates'];assert len(cs)==3
for c in cs:
 t=c['job']['taskGroups'][0]['taskSpec'];q=c['job']['allocationPolicy']['instances'][0]['policy'];assert q['provisioningModel']=='SPOT' and q['accelerators']==[{'type':'nvidia-tesla-t4','count':1}] and t['maxRetryCount']==0
assert 'source_epoch=159,next_epoch=160' in (D/'cloud_check.py').read_text()
proof=dict(passed=True,dropout_probability=.1,parameters=25159,parent_epoch=159,eval_bitwise_equal_parent=True,train_stochastic=True,restored_rng_forward_bitwise=True,optimizer_executed=False)
(R/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
