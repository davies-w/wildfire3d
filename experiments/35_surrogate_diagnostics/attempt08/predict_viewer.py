"""Frozen CPU inference only. No optimizer, gradients or model selection."""
from pathlib import Path
import json,sys,hashlib,base64,time
import numpy as np,torch
R=Path(__file__).parent;S=R.parent/'attempt07';sys.path.insert(0,str(S));from model import HotUNet,metrics
torch.set_num_threads(4);torch.set_grad_enabled(False);cases=json.loads((R/'cases.json').read_text());frozen=json.loads((R/'results/model-freeze.json').read_text());report=json.loads((R/'data/training-report.json').read_text());geoms=np.load(R/'data/geometries.npz');fit={c['case'] for c in json.loads((S/'cases.json').read_text()) if c['split']=='train'};scale=max(float(geoms[n].max()) for n in fit);out=R/'data/viewer';(out/'cases').mkdir(parents=True,exist_ok=True)
coords=np.stack(np.meshgrid(*[(np.arange(n)+.5)/n*2-1 for n in [48,32,32]],indexing='ij')).astype(np.float32)
def encode(mask):return base64.b64encode(np.flatnonzero(mask).astype('<u2').tobytes()).decode()
rows={};inputs=[];truth={};started=time.monotonic()
for c in cases:
 n=c['case'];a=np.radians(c['angle_deg']);cond=np.array([c['wind_speed']/5,c['moisture']/.3,c['loading_multiplier']/1.3,c['crown_height_m']/10,np.cos(a),np.sin(a)],np.float32);inputs.append(np.concatenate([geoms[n]/scale,coords,np.broadcast_to(cond[:,None,None,None],(6,48,32,32))]));z=np.load(R/'data/labels'/(n+'.npz'));truth[n]=(z['packed'],z['time']);rows[n]=dict(case=n,frames={},fuel=encode(geoms[n].sum(0)>0))
inputs=np.stack(inputs);audit=[]
for modelreport in report['models']:
 f=modelreport['frame'];ep=modelreport['epochs'];p=R/'data/models'/f'time-{f:03}-epoch-{ep:03}.pt';assert hashlib.sha256(p.read_bytes()).hexdigest()==frozen['files'][str(p.relative_to(R))];m=HotUNet();s=torch.load(p,map_location='cpu',weights_only=False);m.load_state_dict(s['model']);m.eval();counts=[]
 for k in range(0,len(cases),4):
  pred=(m(torch.from_numpy(inputs[k:k+4]))>=0).numpy()
  for j,mask in enumerate(pred):
   c=cases[k+j];n=c['case'];packed,t=truth[n];y=np.unpackbits(packed[f],count=49152).reshape(48,32,32).astype(bool);v=[int((mask&y).sum()),int((mask&~y).sum()),int((~mask&y).sum()),int((~mask&~y).sum())];counts.append(v);rows[n]['frames'][str(f*2)]=dict(truth=encode(y),prediction=encode(mask),actual_time_s=float(t[f]),metrics=metrics(v))
 for n,r in rows.items():(out/'cases'/(n+'.json')).write_text(json.dumps(r,separators=(',',':')))
 audit.append(dict(nominal_time_s=f*2,checkpoint_sha256=frozen['files'][str(p.relative_to(R))],epoch=ep,counts=counts));print('PREDICTED',f*2,'elapsed',round(time.monotonic()-started),flush=True)
index=dict(cases=cases,times=[m['nominal_time_s'] for m in report['models']],shape=[48,32,32],dx_m=.5,threshold_C=50,classification_threshold=.5,backend='Frozen PyTorch CPU inference; no fitting. Precomputed exact-case outputs, not browser training or arbitrary-input inference.',source='FDS gas-temperature labels; previously examined test cases. No physical validation.',model_stop_reasons={str(m['nominal_time_s']):m['reason'] for m in report['models']})
(out/'index.json').write_text(json.dumps(index,separators=(',',':')));(R/'results/prediction-audit.json').write_text(json.dumps(dict(backend='CPU inference only',density_scale=scale,cases=[c['case'] for c in cases],models=audit,elapsed_s=time.monotonic()-started),indent=2))
