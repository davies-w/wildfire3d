"""Forward-only validation; no optimizer or local training/backward."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import sys,json,hashlib,io
import numpy as np,torch
R=Path(__file__).resolve().parent;D=R/'data/training';sys.path.insert(0,str(D))
from model import Transition
schema=json.loads((D/'schema.json').read_text());rot=schema['rotations'][0];a=np.load(D/'data/sequences.npz');c=np.load(D/'data/cones.npz')
assert c['parameters'].shape==(2080,91,5) and c['active'].shape==(2080,91) and np.array_equal(a['time'],c['time']);assert np.isfinite(c['parameters']).all()
sets={s:{tuple(schema['cases'][i]['physical_key']) for i in rot[s]} for s in ['train','validation','test']}
assert all(not sets[x]&sets[y] for x,y in [('train','validation'),('train','test'),('validation','test')]);assert [len(rot[s]) for s in sets]==[1662,210,208]
torch.manual_seed(3516);m=Transition('gated');assert sum(p.numel() for p in m.parameters())==25549;assert not any(isinstance(v,torch.nn.Dropout) for v in m.modules());assert m.cell.num_layers==1 and m.cell.input_size==41
with torch.no_grad():
 x=torch.zeros(4,8,4);u=torch.ones(4,9);m.eval();q,_=m.step(x,u);cone=m.last_cone.clone();assert cone.shape==(4,5) and torch.isfinite(cone).all()
 f=io.BytesIO();torch.save(m.state_dict(),f);f.seek(0);n=Transition('gated');n.load_state_dict(torch.load(f,weights_only=False));n.eval();assert torch.equal(q,n(x,u)) and torch.equal(cone,n.last_cone)
 xx=torch.randn(4,12,41);whole,_=m.cell(xx);memory=None;parts=[]
 for j in range(12):v,memory=m.cell(xx[:,j:j+1],memory);parts.append(v)
 assert torch.allclose(torch.cat(parts,1),whole,atol=2e-6,rtol=2e-5)
assert not (D/'data/resume').exists()
proof=dict(passed=True,scope='CPU forward-only; no optimizer or backward. Cloud actual-loss backward and optimizer replay still mandatory.',parameters=25549,gru_layers=1,dropout=False,fresh_seed=3516,split_histories=[1662,210,208],config_disjoint=True,all_label_times_exact=True,serialization_bitwise=True,prefix_equivalent=True,cone_inputs=False,cone_labels_sha256=hashlib.sha256((D/'data/cones.npz').read_bytes()).hexdigest())
(R/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
