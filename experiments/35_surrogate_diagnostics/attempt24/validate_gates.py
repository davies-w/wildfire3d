"""No optimizer: gate semantics, supervised gradient and checkpoint buffer checks."""
import json,io,torch
from pathlib import Path
from model import Transition
R=Path(__file__).resolve().parent;torch.set_num_threads(4);mean=torch.tensor([.2,.3,.4,.5]);std=torch.tensor([.5,.6,.7,.8]);history=torch.ones(3,4,4);external=torch.zeros(3,9);external[:,-1]=1
m=Transition('gated');m.set_normalization(mean,std)
with torch.no_grad():
 m.head.bias.copy_(torch.tensor([.1,.2,.3,.4]));m.gate_head.bias.fill_(-80)
p,_=m.step(history,external);assert torch.equal(p[:,:2],history[:,-1,:2]);assert torch.allclose(torch.sinh(p[:,2]*std[2]+mean[2]),torch.zeros(3),atol=1e-6);assert torch.allclose(p[:,3],history[:,-1,3]+.4)
with torch.no_grad():m.gate_head.bias.fill_(80)
popen,_=m.step(history,external);assert torch.allclose(popen,history[:,-1]+torch.tensor([.1,.2,.3,.4]),atol=1e-6)
with torch.no_grad():m.gate_head.bias.fill_(0)
m.zero_grad();p,_=m.step(history,external);loss=p.square().mean()+.1*torch.nn.functional.binary_cross_entropy_with_logits(m.last_gate_logits,torch.zeros(3,3));loss.backward();assert m.gate_head.weight.grad.abs().sum()>0;assert all(x.grad is None or torch.isfinite(x.grad).all() for x in m.parameters())
b=io.BytesIO();torch.save(m.state_dict(),b);b.seek(0);clone=Transition('gated');clone.load_state_dict(torch.load(b,weights_only=True));assert torch.equal(m(history,external),clone(history,external))
(R/'results/gate-preflight.json').write_text(json.dumps({'passed':True,'local_training':False,'parameters':sum(p.numel() for p in m.parameters()),'checks':['closed water/fuel gates preserve mass','closed gas gate suppresses rate not delta','closed gates do not freeze heating','gates reopen without absorbing latch','supervised gate gradients finite nonzero','normalization buffers serialize exactly']},indent=2));print('Gate semantics passed')
