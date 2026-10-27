"""Frozen model TRAIN-only matched-condition response; descriptive, no fitting."""
from pathlib import Path
import ast,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02'
sys.path.insert(0,str(D));from model import Transition
torch.set_num_threads(4)
a=np.load(D/'data/sequences.npz');m=json.loads((D/'schema.json').read_text());ids=torch.tensor(m['rotations'][0]['train']);raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);scale=torch.tensor(m['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(m['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
names={'history_at','advance','predictions'};nodes=[n for n in ast.parse((D/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);ns=dict(torch=torch,external=external);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-inference','exec'),ns)
mask=times[ids,1:]<=32.2
peaks={'truth':raw[ids,1:,2].masked_fill(~mask,-float('inf')).amax(1).numpy()}
with torch.inference_mode():
 for mode in ['one_step','rollout']:
  pred=ns['predictions'](model,z,ids,mode=='rollout');gas=torch.sinh(pred[:,:,2]*std[2]+mean[2])*scale[2];assert torch.isfinite(gas).all();peaks[mode]=gas.masked_fill(~mask,-float('inf')).amax(1).numpy()
configs={}
for j,i in enumerate(ids.tolist()):
 c=int(a['configuration'][i]);r=configs.setdefault(c,dict(key=m['cases'][i]['physical_key'],values={k:[] for k in peaks}))
 assert r['key']==m['cases'][i]['physical_key']
 for k,v in peaks.items():r['values'][k].append(float(v[j]))
for r in configs.values():r['values']={k:float(np.mean(v)) for k,v in r['values'].items()}
results={}
for dim,name in enumerate(['height_m','moisture_ratio','loading_multiplier','wind_m_s','ignition_angle_deg']):
 groups={}
 for c,r in configs.items():groups.setdefault(tuple(v for j,v in enumerate(r['key']) if j!=dim),[]).append((c,r))
 pairs=[]
 for group in groups.values():
  if len(group)<2:continue
  group.sort(key=lambda x:x[1]['key'][dim]);(cl,lo),(ch,hi)=group[0],group[-1];delta={k:hi['values'][k]-lo['values'][k] for k in peaks};pairs.append(dict(low_configuration=cl,high_configuration=ch,low_value=lo['key'][dim],high_value=hi['key'][dim],delta_peak_kg_s=delta,truth_peak_scale=max(lo['values']['truth'],hi['values']['truth'],1e-12)))
 x=np.array([r['delta_peak_kg_s']['truth'] for r in pairs]);summary={}
 for mode in ['one_step','rollout']:
  y=np.array([r['delta_peak_kg_s'][mode] for r in pairs]);material=np.array([abs(r['delta_peak_kg_s']['truth'])>.1*r['truth_peak_scale'] for r in pairs]);summary[mode]=dict(response_projection=float(x@y/(x@x)) if x@x>0 else None,material_pairs=int(material.sum()),sign_agreement_material=float(np.mean(np.sign(x[material])==np.sign(y[material]))) if material.any() else None,median_normalized_delta_error=float(np.median([abs(r['delta_peak_kg_s'][mode]-r['delta_peak_kg_s']['truth'])/r['truth_peak_scale'] for r in pairs])) if pairs else None)
 results[name]=dict(matched_extreme_pairs=len(pairs),summary=summary,pairs=pairs)
out=dict(train_only=True,optimizer_updates=0,checkpoint_epoch=ck['epoch'],histories=len(ids),configurations=len(configs),scope='Descriptive matched TRAIN configurations: vary one physical-key coordinate, other four exactly fixed; average replicas, compare min/max available coordinate. Gas peak uses actual saved endpoints<=32.2s. Projection is sum(true_delta*predicted_delta)/sum(true_delta^2), not fitted model performance, a causal effect, or a universal sensitivity. Observed-history one-step retains recurrent memory driven by observed history. Same nominal peak can occur at different times. Angle endpoints are an exploratory coordinate comparison, not a circular trend. No validation/test use or optimizer updates.',conditions=results)
(R/'results/condition-response-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{a:b for a,b in v.items() if a!='pairs'} for k,v in results.items()},indent=2))
