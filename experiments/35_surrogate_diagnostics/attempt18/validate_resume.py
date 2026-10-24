"""Actual checkpoint restoration without optimization; mock GPU RNG device boundary."""
from pathlib import Path
import ast,json,random,io
import numpy as np
import torch
from unittest.mock import patch
from model import Transition
R=Path(__file__).resolve().parent;c=torch.load(R/'data/resume/fold15.pt',map_location='cpu',weights_only=False)
source=ast.parse((R/'worker.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='restore_rng');ns={'torch':torch,'np':np,'random':random};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-restore-function','exec'),ns)
class SimulatedGpuState:
 def __init__(self,value):self.value=value;self.calls=0
 def cpu(self):self.calls+=1;return self.value
wrapped=[SimulatedGpuState(s) for s in c['rng']['cuda']];saved=dict(c['rng'],cuda=wrapped)
def setter(states):
 assert all(isinstance(s,torch.Tensor) and s.dtype==torch.uint8 and s.device.type=='cpu' for s in states)
 assert all(torch.equal(s,t) for s,t in zip(states,c['rng']['cuda']))
with patch.object(torch.cuda,'set_rng_state_all',side_effect=setter):
 ns['restore_rng'](saved);a=torch.rand(8);b=np.random.random(8);d=random.random();ns['restore_rng'](saved);assert torch.equal(a,torch.rand(8));assert np.array_equal(b,np.random.random(8));assert d==random.random()
assert all(s.calls==2 for s in wrapped)
m=Transition(c['kind']);m.load_state_dict(c['model']);o=torch.optim.AdamW(m.parameters(),lr=.0003,weight_decay=1e-4);o.load_state_dict(c['optimizer']);assert len(o.state)==len(c['optimizer']['state'])
x=torch.zeros(4,4,3);u=torch.zeros(4,9);u[:,-1]=1;y=m(x,u);assert torch.isfinite(y).all();buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(c['kind']);m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(y,m2(x,u))
(R/'results/resume-preflight.json').write_text(json.dumps(dict(passed=True,checkpoint_epoch=c['epoch'],optimization_performed=False,gpu_state_cpu_conversion_exercised=True,cpu_numpy_python_rng_replayed=True,optimizer_loaded=True,model_replay_exact=True,actual_gpu_check_required_in_worker=True),indent=2));print('RESUME PREFLIGHT PASSED; no optimization')
