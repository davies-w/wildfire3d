"""Descriptive, configuration-weighted cone height associations; no causal claims."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'data/pivot-analysis';D.mkdir(exist_ok=True)
s=json.loads((R/'data/training03/schema.json').read_text());c=np.load(R/'data/training03/data/cones.npz');q=np.load(R/'data/training03/data/sequences.npz')
names=s['external_names'][:7]+['moisture_fraction','ignition_angle_deg']
x=np.column_stack([q['geometry'],np.array([v['physical_key'] for v in s['cases']])[:,[1,4]]])
p=c['parameters'];active=c['active'].astype(bool);t=c['time'];a=np.deg2rad(p[:,:,1]);top=p[:,:,0]+np.maximum(0,p[:,:,2]*np.cos(a)+p[:,:,3]*np.sin(a))
configs=np.unique(q['configuration']);rng=np.random.default_rng(3516)
def quant(v):
 return dict(zip(['min','p05','median','p95','max'],map(float,np.quantile(v,[0,.05,.5,.95,1]))))
out={'scope':'All 2080 historical histories; aggregate replicas to 2040 configurations; observational associations, not causal effects. Active frames only. Main analysis after20s. Cone apex candidates depend on crown height; cone top may extend beyond observed crop.','periods':{}}
fig,axs=plt.subplots(2,3,figsize=(13,7));fig.suptitle('Simulation-derived cone apex after 20 s · plotted groups n≥20; correlations use all configurations')
for period,mask in [('all',active),('after20',active&(t>20))]:
 rows=[]
 for i in range(len(p)):
  m=mask[i]
  if not m.any():continue
  rows.append((i,float(p[i,m,0].mean()),float((p[i,m,0]==0).mean()),float(p[i,m,0].max()),float(top[i,m].mean()),float(top[i,m].max())))
 rows=np.array(rows);ids=rows[:,0].astype(int);group=[];features=[]
 for key in configs:
  use=q['configuration'][ids]==key
  if use.any():group.append(rows[use,1:].mean(axis=0));features.append(x[ids[use]].mean(axis=0))
 g=np.array(group);f=np.round(np.array(features),6);y=g[:,0];corr=[]
 for k,name in enumerate(names):
  rho=float(spearmanr(f[:,k],y).statistic);bs=[]
  for _ in range(500):
   ix=rng.integers(0,len(y),len(y));bs.append(spearmanr(f[ix,k],y[ix]).statistic)
  corr.append(dict(feature=name,spearman=rho,bootstrap95=list(map(float,np.quantile(bs,[.025,.975])))))
 groups={}
 for k in [0,1,2,7,8]:
  groups[names[k]]=[dict(value=float(v),n=int((f[:,k]==v).sum()),mean_pivot_m=float(y[f[:,k]==v].mean())) for v in np.unique(f[:,k])]
 out['periods'][period]=dict(histories=len(rows),configurations=len(g),active_frame_count=int(mask.sum()),configuration_mean_ground_fraction=float(g[:,1].mean()),configuration_mean_pivot_m=quant(y),mean_pivot_m=float(y.mean()),configuration_peak_pivot_m=quant(g[:,2]),configuration_mean_cone_top_m=quant(g[:,3]),configuration_peak_cone_top_m=quant(g[:,4]),correlations=corr,grouped_means=groups)
 if period=='after20':
  for ax,k in zip(axs.flat[:5],[0,1,2,7,8]):
   vals=[v for v in groups[names[k]] if v['n']>=20];ax.plot([v['value'] for v in vals],[v['mean_pivot_m'] for v in vals],'o-');ax.set(xlabel=names[k],ylabel='Mean active apex height (m)');ax.set_ylim(bottom=0);ax.grid(alpha=.2)
  axs.flat[5].hist(y,bins=30);axs.flat[5].set(xlabel='Configuration mean apex height (m)',ylabel='Configurations')
fig.tight_layout();fig.savefig(D/'pivot-associations.png',dpi=160);plt.close(fig)
(D/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['periods']['after20'],indent=2))
