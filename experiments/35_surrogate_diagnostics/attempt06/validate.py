from pathlib import Path
import json,ast,torch,numpy as np,hashlib,io
from coordinate_model import CoordinateMLP,physical
R=Path(__file__).parent
for p in R.glob('*.py'):ast.parse(p.read_text())
plan=json.loads((R/'coverage-plan.json').read_text());assert set(plan['train_frames']).isdisjoint(plan['validation_frames']);assert sorted(plan['train_frames']+plan['validation_frames'])==list(range(91));assert len(plan['train_frames'])==82 and len(plan['validation_frames'])==9
c=json.loads((R/'cases.json').read_text());assert len(c)==1 and c[0]['split']=='train';a=np.load(R/'data/fields'/(c[0]['case']+'.npy'),mmap_mode='r');assert a.shape==(91,6,48,32,32);assert np.isfinite(a).all()
torch.manual_seed(3506);m=CoordinateMLP();x=torch.randn(10,4)
with torch.no_grad():p=m(x);assert p.shape==(10,6) and torch.isfinite(p).all();assert (physical(p,c[0]['wind_speed'])[:,1]>=0).all()
b=io.BytesIO();torch.save(m.state_dict(),b);b.seek(0);m.load_state_dict(torch.load(b,weights_only=True))
with torch.no_grad():assert torch.equal(p,m(x))
(R/'results/preflight.json').write_text(json.dumps({'passed':True,'training_frames':82,'heldout_time_frames':9,'training_cells_per_epoch':82*48*32*32,'parameters':sum(p.numel() for p in m.parameters()),'synthetic_forward_replay':True,'scope':'CPU synthetic inference only, no training. CUDA replay mandatory.'},indent=2))
print('Preflight passed; no optimization')
