"""Frozen selected-model CPU inference only; all 2..32 second horizons."""
from pathlib import Path
import json,numpy as np,torch
from model import Transition
R=Path(__file__).resolve().parent;D=R/'data/scenario_horizons';D.mkdir(exist_ok=True)
torch.set_num_threads(4)
a=np.load(R/'data/sequences.npz');meta=json.loads((R/'schema.json').read_text());i=int(meta['rotations'][0]['test'][0]);ck=torch.load(R/'data/collected/fold01-selected.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
s=torch.tensor(a['state'][i]);t=torch.tensor(a['time'][i]);scale=torch.tensor(meta['physical_encoding_scales']);mean=ck['mean'].cpu();std=ck['std'].cpu();z=(torch.asinh(s/scale)-mean)/std;dt=t[1:]-t[:-1];on=(20-t[:-1]).clamp_min(0).minimum(dt)/dt;g=torch.tensor(a['geometry'][i]);ext=torch.cat([g[None].expand(90,-1),on[:,None],dt[:,None]],-1)/torch.tensor(meta['external_scales']);origins=torch.arange(90);hist=z[(origins[:,None]+torch.arange(-3,1)).clamp_min(0)]
with torch.no_grad():
 prefix,_=model.cell(model.inputs(hist,ext)[None]);memory=torch.cat([torch.zeros(1,32),prefix[0,:-1]],0);preds={}
 for h in range(1,17):
  p,memory=model.step(hist,ext[(origins+h-1).clamp_max(89)],memory);hist=torch.cat([hist[:,1:],p[:,None]],1);preds[str(h)]=(torch.sinh(p[:91-h]*std+mean)*scale).numpy()
checks={}
for h in [1,4,8,16]:
 v=np.load(R/f'data/collected/fold01-horizon{h:02}-predictions.npz');j=int(np.flatnonzero(v['case_indices']==i)[0]);expected=v['predicted_physical'][j];delta=abs(preds[str(h)]-expected);checks[str(h)]=delta.max(0).tolist();assert np.allclose(preds[str(h)],expected,atol=0.002,rtol=0.002)
np.savez_compressed(D/'predictions.npz',time=t.numpy(),truth=s.numpy(),**preds)
(D/'verification.json').write_text(json.dumps(dict(case=meta['cases'][i]['case'],no_fitting=True,model='fold01-selected gated',cpu_vs_saved_gpu_max_abs_difference=checks),indent=2))
print(checks)
