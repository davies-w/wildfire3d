"""Scientific plots of all existing isolated cases, preserving full time resolution."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build import ROOT
D=ROOT/'data/single-dynamics-extended';O=ROOT/'results/visuals';O.mkdir(exist_ok=True)
cs=json.loads((ROOT/'cases.json').read_text())
colors={'FDS':'#222222','Old graph':'#b25a6a','Constrained ROM':'#cc8a23','Full-rollout RNN':'#1976ad'}
for metric in ['temperature','mass']:
 fig,axes=plt.subplots(3,6,figsize=(20,9),sharex=True)
 for row,typ in enumerate('ABC'):
  for col in range(6):
   name=f't26_single_{typ}_{col}';c=next(c for c in cs if c['case']==name);r=np.load(D/(name+'-recurrent.npz'));q=np.load(D/(name+'-rom.npz'));old=np.load(ROOT/'data/development-predictions'/(name+'__single_composed.npz'));n=r['truth'].shape[1]//2;ax=axes[row,col]
   if metric=='temperature':series={'FDS':r['truth'][:,:n].mean(1)*1000+20,'Old graph':old['state'][:,:,0].mean(1)*1000+20,'Constrained ROM':q['prediction'][:,:n].mean(1)*1000+20,'Full-rollout RNN':r['prediction'][:,:n].mean(1)*1000+20}
   else:series={'FDS':r['truth'][:,n:].mean(1),'Old graph':old['state'][:,:,1].mean(1),'Constrained ROM':q['prediction'][:,n:].mean(1),'Full-rollout RNN':r['prediction'][:,n:].mean(1)}
   ax.axvspan(0,c['duration'],color='.9',zorder=0)
   for label,y in series.items():ax.plot(r['time'],y,label=label,color=colors[label],lw=1.5,ls='--' if label=='Old graph' else '-')
   ax.set_title(f"{typ}_{col} · {c['split']}\nheater ×{c['strength']}, {c['duration']} s",fontsize=10)
   ax.set_xlim(0,180);ax.set_xticks([0,60,120,180]);ax.tick_params(labelsize=9);ax.grid(alpha=.15)
   if row==2:ax.set_xlabel('Time (s)')
   if col==0:ax.set_ylabel('Regional mean T (°C)' if metric=='temperature' else 'Mean remaining mass fraction')
   if metric=='mass':ax.set_ylim(-.02,1.02)
 handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=4,bbox_to_anchor=(.5,.947),frameon=False)
 fig.suptitle('Autonomous isolated-tree response — '+('temperature' if metric=='temperature' else 'remaining wet + solid mass'),fontsize=16,y=.995)
 fig.text(.5,.012,'All 18 isolated cases · new models fit separately per fixed tree type · 4 train / 2 validation each · validation selects checkpoints\nUnweighted occupied region/fuel-class means; errors are computed before spatial averaging · shading: artificial heater active · no energy-balance guarantee',ha='center',fontsize=10)
 fig.tight_layout(rect=[0,.07,1,.91]);fig.savefig(O/f'single-dynamics-{metric}.png',dpi=160);plt.close(fig)
