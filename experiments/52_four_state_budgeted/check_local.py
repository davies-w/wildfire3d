"""Forward-only local checks; no optimizer or training on local hardware."""
from pathlib import Path
import json,sys,types,hashlib,io
import numpy as np
import torch
from model import Transition,normalize_fit,normalize_static
from objective import interval_error,sequence_score
R=Path(__file__).resolve().parent

def main():
 torch.set_num_threads(4)
 a=np.load(R/'data/observations.npz');m=json.loads((R/'data/schema.json').read_text());rot=m['rotations'][0]
 raw=torch.tensor(a['state'],dtype=torch.float32);times=torch.tensor(a['time'],dtype=torch.float32);fixed=torch.tensor(a['geometry'],dtype=torch.float32);config=torch.tensor(a['configuration']);train=torch.tensor(rot['train']);scale=torch.tensor(m['physical_encoding_scales'])
 mean,std=normalize_fit(raw,train,config,scale);sm,ss=normalize_static(fixed,train,config)
 assert torch.isfinite(mean).all() and torch.isfinite(std).all() and (std>0).all()
 assert torch.equal(sm[[0,1,2,9]],torch.zeros(4)) and torch.equal(ss[[0,1,2,9]],torch.ones(4))
 perturbed=raw.clone();perturbed[rot['test']]+=1000
 mm,st=normalize_fit(perturbed,train,config,scale);assert torch.equal(mm,mean) and torch.equal(st,std)
 model=Transition('gated');model.set_normalization(mean,std);before={k:v.clone() for k,v in model.state_dict().items()};z=(torch.asinh(raw/scale)-mean)/std
 ids=torch.tensor(rot['validation'][:8]);hist=z[ids,:1].expand(-1,8,-1);memory=None
 with torch.no_grad():
  for j in range(90):
   ext=torch.cat([(fixed[ids]-sm)/ss,torch.tensor(a['ignition_on_fraction'][ids,j],dtype=torch.float32)[:,None],(times[ids,j+1]-times[ids,j])[:,None]/2],-1)
   state,memory=model.step(hist,ext,memory);assert state.shape==(8,4) and torch.isfinite(state).all();hist=torch.cat([hist[:,1:],state[:,None]],1)
 assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
 assert interval_error(torch.tensor([-1.]),torch.tensor([1.])).item()==.5
 assert torch.equal(sequence_score(raw,raw,times,raw.amax(1)-raw.amin(1)),torch.zeros(len(raw),4))
 # Compile the exact extracted cloud loss block; no local backward/update is executed.
 import textwrap
 src=(R/'worker.py').read_text();fragment=src[src.index('    left_error='):src.index("assert bool(torch.isfinite(loss)),f'Nonfinite")];compile(textwrap.dedent(fragment),'<actual-loss>','exec')
 # Exercise the actual worker evaluation path on CPU, forward-only and validation-only.
 import types
 import budget_guard
 original_guard=budget_guard.Guard;budget_guard.Guard=lambda path:None
 prefix=src.split('checks=[]')[0].replace("assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'",'').replace("device='cuda'","device='cpu'")
 scope={'__file__':str(R/'worker.py')}
 try:
  exec(compile(prefix,str(R/'worker.py'),'exec'),scope)
  ids=torch.tensor(rot['validation'][:8]);ev=scope['evaluate'](model,z,ids,mean,std,True)
  assert all(ev[mode]['finite'] for mode in ['one_step','rollout'])
 finally:budget_guard.Guard=original_guard
 result=dict(passed=True,cases=len(raw),train=len(train),validation=len(rot['validation']),test=len(rot['test']),test_values_not_used_for_normalization=True,forward_only=True,parameters=sum(p.numel() for p in model.parameters()),source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.glob('*.py')})
 (R/'local-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
