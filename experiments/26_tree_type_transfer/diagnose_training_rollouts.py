"""Post-test in-sample audit; never refits or modifies frozen models/test predictions."""
import json,hashlib,time
import numpy as np
import torch
from build import ROOT
from model_data import geometry
from graph_model import ComponentGraph
freeze=json.loads((ROOT/'results/prediction-freeze.json').read_text())
for f,h in freeze['files'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
out=ROOT/'data/development-predictions';out.mkdir(exist_ok=True);torch.set_num_threads(4)
models={}
for label,filename,independent in [('single_composed','single-only.pt',False),('pair_adapted','pair-adapted.pt',False),('independent_additive','single-only.pt',True)]:
 m=ComponentGraph();m.load_state_dict(torch.load(ROOT/'data/models'/filename,weights_only=True));m.eval();models[label]=(m,independent)
rows=[]
for c in json.loads((ROOT/'cases.json').read_text()):
 if c['split'] not in ['train','validation']:continue
 d=geometry(c);a=np.load(ROOT/'data/extracted'/(c['case']+'.npz'));raw=a['state'].reshape(len(a['time']),-1,6)[:,d['indices']];tt=np.arange(0,182,2)
 actual=np.stack([np.interp(tt,a['time'],raw[:,j,k]) for j in range(raw.shape[1]) for k in range(6)],axis=1).reshape(len(tt),raw.shape[1],6)
 schedule=[c['strength'] if t+1<c['duration'] else 0. for t in tt[:-1]]
 for label,(m,independent) in models.items():
  with torch.no_grad():state,heat,rate=(m.additive_rollout if independent else m.rollout)(**{k:d[k] for k in ['static','xyz','instance','heater_xyz']},schedule=schedule)
  s,h,r=[v.numpy() for v in [state,heat,rate]]
  np.savez_compressed(out/f"{c['case']}__{label}.npz",time=tt,state=s,heat=h,rate=r,indices=d['indices'],instance=d['instance'].numpy(),fuel=d['fuel'].numpy())
  rows.append(dict(case=c['case'],split=c['split'],family=c['family'],model=label,temperature_MAE_C=float(abs(s[:,:,0]*1000+20-actual[:,:,0]).mean()),mass_fraction_MAE=float(abs(s[:,:,1]-actual[:,:,1]/d['static'][:,9].numpy()).mean())))
 print(c['case'],flush=True)
(ROOT/'results/training-rollout-audit.json').write_text(json.dumps(dict(frozen_hashes_verified=len(freeze['files']),mode='Autonomous from initial conditions; no FDS teacher forcing; no refitting',metrics=rows),indent=2))
