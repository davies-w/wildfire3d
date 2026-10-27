"""CPU structural/report tests only; never optimize parameters."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];D=R/'data/model-pair';sys.path.insert(0,str(D))
source=(R.parent/'35_surrogate_diagnostics/attempt25/validate.py').read_text()
header=source[:source.index('assert raw.shape')].replace("R=Path(__file__).resolve().parent",'R=Path('+repr(str(D))+')')
body=source[source.index('dt=times[:,1:]'):source.index('for h in [1,8,16,32]:')]
body=body.replace("for kind in ['control']:","for kind in ['control','gated']:")
body=body.replace("assert torch.allclose(y,x[:,-1],atol=1e-6,rtol=1e-6)","assert kind=='gated' or torch.allclose(y,x[:,-1],atol=1e-6,rtol=1e-6)")
(D/'results').mkdir(exist_ok=True)
ns={'__file__':str(D/'validate.py')};exec(compile(header+body,'pair-offline','exec'),ns)
for check in ns['checks']:
 if check['kind']=='gated':check['checks'][0]='Three soft gates; initial gas suppression sigmoid(4)'
import torch,numpy as np
from model import Transition,normalize_fit
raw=ns['raw'];a=ns['a'];rot=ns['meta']['rotations'][0];ids=torch.tensor(rot['train']);mean,std=normalize_fit(raw,ids,ns['config'],ns['scale']);alter=raw.clone();alter[rot['test']+rot['validation']]+=1e5
m2,s2=normalize_fit(alter,ids,ns['config'],ns['scale']);assert torch.equal(mean,m2) and torch.equal(std,s2)
for h in (1,8,16,32):
 windows=list(range(91-h));assert len(windows)==91-h and windows[-1]+h==90
models={}
for kind in ('control','gated'):
 torch.manual_seed(3516);models[kind]=Transition(kind)
for n,p in models['control'].named_parameters():assert torch.equal(p,dict(models['gated'].named_parameters())[n])
g=models['gated'];g.set_normalization(mean,std);z=(torch.asinh(raw/ns['scale'])-mean)/std;ii=ids[:4];hist=ns['ns']['history_at'](z,ii,torch.zeros_like(ii));state,_=g.step(hist,ns['external'][ii,0]);target=torch.tensor(a['gate_targets'][ii,0]);mask=torch.tensor(a['gate_supervised'][ii,0]);loss=(torch.nn.functional.binary_cross_entropy_with_logits(g.last_gate_logits,target,reduction='none')*mask).sum();loss.backward();assert g.gate_head.bias.grad is not None and torch.isfinite(g.gate_head.bias.grad).all()
proof=dict(passed=True,training=False,optimizer_created=False,arms=[dict(kind=k,parameters=sum(p.numel() for p in v.parameters())) for k,v in models.items()],shared_initial_parameters_exact=True,heldout_normalization_invariant=True,gate_bce_gradient_finite=True,windows_per_history=[90,83,75,59],checks=ns['checks'])
(R/'results/model-pair-validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
