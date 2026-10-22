"""Synthetic interface checks only; no laptop optimization/training."""
import json,numpy as np,torch
from pathlib import Path
from models import SpatialHeads
from losses import revised
from worker import inputs
from matched_losses import objective_for
R=Path(__file__).parent
def main():
 from validate_interpolation import validate
 validate()
 torch.set_num_threads(2);cs=json.loads((R/'cases.json').read_text());z=np.load(R/'data/geometries.npz');c=cs[0];x,g,s=inputs(c,np.array([0.,22.]),z[c['case']],'cpu');m=SpatialHeads()
 with torch.no_grad():
  p=m(x,g,s);assert p.shape==(2,6,48,32,32) and torch.isfinite(p).all();assert revised(p,p).abs()<1e-5
  ambient=torch.ones_like(p[0,5])*1.67506325
  for arm in ['control','dose_background','physical_low','dose_repeat']:
   assert objective_for(arm,p,p,ambient).abs()<1e-5
   assert torch.isfinite(objective_for(arm,p,torch.zeros_like(p),ambient))
  q=10*torch.expm1(p[:,1]);assert (q>=0).all();assert s[0].sum()>0 and s[1].sum()==0
  zero=torch.zeros_like(p);assert torch.isfinite(revised(p,zero));assert revised(p,zero)>revised(zero,zero)
 assert len({c['configuration'] for c in cs})==152 and all(c['split']!='test' for c in cs)
 (R/'results/preflight.json').write_text(json.dumps(dict(passed=True,shape=list(p.shape),parameters=sum(p.numel() for p in m.parameters()),scope='Synthetic forward/loss identity/finite weak-target/source-removal/split checks; no training or physical validation'),indent=2));print('PRECHECK PASSED')
if __name__=='__main__':main()
