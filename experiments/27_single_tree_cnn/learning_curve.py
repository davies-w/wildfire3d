"""Show per-case held-out errors and mean learning curves; no smoothing over failures."""
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
R=Path(__file__).parent;rows=json.loads((R/'results/test-summary.json').read_text())['cases'];fig,axes=plt.subplots(1,3,figsize=(12,4))
for ax,key,label in zip(axes,['hot_union_temperature_MAE_C','flame_proxy_IoU','velocity_vector_MAE_m_s'],['Hot-region temperature MAE (°C) ↓','Combustion mask overlap ↑','All-volume velocity error (m/s) ↓']):
 for family,color in [('cnn','steelblue'),('interpolation','darkorange')]:
  means=[]
  for n in [8,16,32]:
   vals=[r[key] for r in rows if r['model']==family+'_'+str(n) and r[key] is not None];means.append(np.mean(vals));ax.scatter(np.full(len(vals),n),vals,color=color,alpha=.35,s=18)
  ax.plot([8,16,32],means,'o-',color=color,label=family)
 ax.set(xlabel='Independent training simulations',ylabel=label,xticks=[8,16,32]);ax.grid(alpha=.2)
axes[0].legend();fig.suptitle('Six fixed held-out cases: dots = cases, lines = mean; one CNN seed');fig.tight_layout();(R/'results/visuals').mkdir(exist_ok=True);fig.savefig(R/'results/visuals/learning-curve.png',dpi=150)
