"""CUDA synthetic AdamW continuation replay for both arms before data fitting."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import io,json,torch,numpy as np,random
from model import Transition
from runtime import upload
torch.use_deterministic_algorithms(True);torch.set_num_threads(4);assert torch.cuda.is_available()
checks=[]
for kind in ('control','gated'):
 torch.manual_seed(3516);np.random.seed(3516);random.seed(3516);m=Transition(kind).cuda();opt=torch.optim.AdamW(m.parameters(),lr=3e-4,weight_decay=1e-4)
 def step(model,optimizer):
  x=torch.randn(4,4,4,device='cuda');u=torch.randn(4,9,device='cuda');u[:,-1]=1;target=torch.randn(4,4,device='cuda');pred=model(x,u);loss=(pred-target).square().mean()
  if kind=='gated':loss+=.1*torch.nn.functional.binary_cross_entropy_with_logits(model.last_gate_logits,torch.ones(4,3,device='cuda'))
  optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();return loss.detach()
 step(m,opt);assert len(opt.state)>0
 buf=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),rng=torch.cuda.get_rng_state_all()),buf)
 expected=step(m,opt);expected_state={k:v.clone() for k,v in m.state_dict().items()}
 buf.seek(0);ck=torch.load(buf,map_location='cuda',weights_only=False);restored=Transition(kind).cuda();restored.load_state_dict(ck['model']);oo=torch.optim.AdamW(restored.parameters(),lr=3e-4,weight_decay=1e-4);oo.load_state_dict(ck['optimizer']);torch.cuda.set_rng_state_all([r.cpu() for r in ck['rng']]);actual=step(restored,oo)
 assert torch.equal(expected,actual) and all(torch.equal(v,restored.state_dict()[k]) for k,v in expected_state.items())
 for p,q in zip(opt.state.values(),oo.state.values()):
  assert p.keys()==q.keys()
  for k in p:assert torch.equal(p[k],q[k]) if torch.is_tensor(p[k]) else p[k]==q[k]
 checks.append(dict(kind=kind,nonempty_optimizer=True,next_update_bitwise_equal=True))
u=json.dumps(dict(passed=True,synthetic_only=True,test_evaluated=False,checks=checks)).encode();upload('optimizer-resume-check.json',u)
