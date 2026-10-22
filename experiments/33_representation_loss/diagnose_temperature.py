"""Forward-only inspection of saved checkpoint; no optimization."""
import sys,json,torch,numpy as np
from pathlib import Path
R=Path(__file__).parent
sys.path.insert(0,str(R/'attempt03'))
from models import SpatialHeads
from worker import inputs
from previous_loss import quantities
torch.set_num_threads(2);m=SpatialHeads();m.load_state_dict(torch.load(R/'attempt03/data/collected/spatial_heads-checkpoint-6000.pt',map_location='cpu',weights_only=False)['model']);g=np.load(R/'data/geometries.npz');rows=[]
for c in json.loads((R/'cases.json').read_text())[:3]:
 raw={};hooks=[head[-1].register_forward_hook(lambda mod,args,out,n=name:raw.update({n:out.detach()})) for name,head in m.heads.items()]
 with torch.no_grad():
  x,d,s=inputs(c,np.array([30.,90.],dtype=np.float32),g[c['case']],'cpu');p=m(x,d,s);t,q,rad=quantities(p)
 rows.append(dict(case=c['case'],temperature_raw_min=float(raw['temperature'].min()),temperature_raw_max=float(raw['temperature'].max()),temperature_min_C=float(t.min()),temperature_max_C=float(t.max()),raw_temperature_clamped_fraction=float((raw['temperature'].abs()>=5).float().mean())))
 for h in hooks:h.remove()
(R/'results/spatial-temperature-diagnostic.json').write_text(json.dumps(rows,indent=2))
