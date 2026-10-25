"""All held-out histories, selected gated models; CPU inference only for initial ramp."""
from pathlib import Path
import json,numpy as np,torch
from model import Transition
R=Path(__file__).resolve().parent;D=R/'data/scenario_gallery';D.mkdir(exist_ok=True);torch.set_num_threads(4)
a=np.load(R/'data/sequences.npz');meta=json.loads((R/'schema.json').read_text());scale=torch.tensor(meta['physical_encoding_scales']);records=[];checks=[];seen=[]
for rot in range(10):
 fold=2*rot+1;ids=np.array(meta['rotations'][rot]['test']);seen.extend(ids.tolist());ck=torch.load(R/f'data/collected/fold{fold:02}-selected.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);model.eval();mean=ck['mean'].cpu();std=ck['std'].cpu()
 s=torch.tensor(a['state'][ids]);t=torch.tensor(a['time'][ids]);g=torch.tensor(a['geometry'][ids]);dt=t[:,1:]-t[:,:-1];on=(20-t[:,:-1]).clamp_min(0).minimum(dt)/dt;ext=torch.cat([g[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);z=(torch.asinh(s/scale)-mean)/std;hist=z[:,0:1].expand(-1,4,-1);memory=None;ramp=[]
 with torch.no_grad():
  for j in range(16):
   p,memory=model.step(hist,ext[:,j],memory);ramp.append((torch.sinh(p*std+mean)*scale).numpy());hist=torch.cat([hist[:,1:],p[:,None]],1)
 ramp=np.stack(ramp,1);one=np.load(R/f'data/collected/fold{fold:02}-horizon01-predictions.npz');six=np.load(R/f'data/collected/fold{fold:02}-horizon16-predictions.npz');assert np.array_equal(one['case_indices'],ids) and np.array_equal(six['case_indices'],ids)
 for j,h in [(0,1),(15,16)]:
  saved=(one if h==1 else six)['predicted_physical'][:,0];delta=abs(ramp[:,j]-saved);assert np.allclose(ramp[:,j],saved,atol=.002,rtol=.002);checks.append(dict(fold=fold,steps=h,max_abs=delta.max(0).tolist()))
 targets=np.arange(1,91);steps=np.minimum(targets,16);origins=targets-steps
 for j,i in enumerate(ids):
  state=a['state'][i];recursive=np.concatenate([ramp[j,:15],six['predicted_physical'][j]],0);series=np.stack([state[1:],state[origins],state[origins]+steps[:,None]*(one['predicted_physical'][j,origins]-state[origins]),recursive]);assert series.shape==(4,90,4)
  key=meta['cases'][i]['physical_key'];records.append(dict(index=int(i),case=meta['cases'][i]['case'],fold=rot,source=meta['cases'][i]['source'],height=float(g[j,0]),loading=float(g[j,1]),wind=float(g[j,2]),angle=float(np.degrees(np.arctan2(float(g[j,4]),float(g[j,3])))%360),water=float(state[0,0]),fuel=float(state[0,1]),time=a['time'][i,1:].tolist(),values=series.tolist()))
assert sorted(seen)==list(range(520));records.sort(key=lambda x:x['index'])
for page in range((len(records)+2)//3):
 payload=json.dumps(records[page*3:page*3+3],separators=(',',':'),allow_nan=False)
 (D/f'page-{page}.js').write_text('window.receivePage('+str(page)+','+payload+');')
(D/'report.html').write_text((R/'gallery.html').read_text().replace('__TOTAL__',str(len(records))))
(D/'verification.json').write_text(json.dumps(dict(histories=len(records),configurations=len(np.unique(a['configuration'])),pages=(len(records)+2)//3,held_out_once_per_model=True,cpu_initial_ramp_vs_saved_gpu=checks,scope='Only initial 1..15-step prefix recomputed with frozen gated model on CPU. Rolling16step values from saved GPU test forecasts. No fitting.'),indent=2));print('Built',len(records),'held-out histories')
