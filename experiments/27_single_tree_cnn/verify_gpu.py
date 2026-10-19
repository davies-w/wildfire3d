"""Check CPU/MPS numerical consistency and optimizer support before using local GPU."""
import copy,json,time
import numpy as np,torch
from cnn import CNN,loss,ROOT
assert torch.backends.mps.is_available()
torch.manual_seed(27);cpu=CNN();gpu=copy.deepcopy(cpu).to('mps');x=torch.randn(2,8);y=torch.randn(2,6,48,32,32)*.1
oc=torch.optim.AdamW(cpu.parameters(),lr=.001);og=torch.optim.AdamW(gpu.parameters(),lr=.001)
with torch.no_grad():initial=float((cpu(x)-gpu(x.to('mps')).cpu()).abs().max())
for i in range(5):
 for model,opt,dev in [(cpu,oc,'cpu'),(gpu,og,'mps')]:
  opt.zero_grad();l=loss(model(x.to(dev)),y.to(dev));l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
with torch.no_grad():
 a=cpu(x);b=gpu(x.to('mps')).cpu();error=float((a-b).abs().max());mae=float((a-b).abs().mean())
assert initial<1e-4 and error<.005,(initial,error)
r=dict(passed=True,initial_max_encoded_error=initial,after_five_updates_max_encoded_error=error,after_five_updates_mean_encoded_error=mae,torch=torch.__version__,device='Apple MPS',scope='Numerical implementation check, not FDS predictive accuracy')
torch.save(gpu.state_dict(),ROOT/'data/gpu-portability.pt')
restored=CNN();restored.load_state_dict(torch.load(ROOT/'data/gpu-portability.pt',map_location='cpu',weights_only=True))
with torch.no_grad():assert torch.allclose(restored(x),gpu(x.to('mps')).cpu(),atol=1e-5,rtol=1e-4)
r['saved_MPS_weights_load_on_CPU_verified']=True
(ROOT/'results/gpu-preflight.json').write_text(json.dumps(r,indent=2));print(r)
