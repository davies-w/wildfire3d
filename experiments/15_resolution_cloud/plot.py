import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from study import ROOT

d=json.loads((ROOT/'results/local_analysis.json').read_text())
fig,axs=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
colors={'coarse':'#b36a27','medium':'#157a99','fine':'#354355','split_fine':'#7555a1','local_fine':'#4b893e','radiation':'#bd4969'}
for mode,ax in zip(['flow','fire'],axs[:2]):
    for c in d['comparisons']:
        if not c['case'].startswith(mode+'_') or c['repeat']!=1:continue
        variant=c['case'][len(mode)+1:]
        error=c['metrics']['wake_u' if mode=='flow' else 'surface_max_C']['rmse']
        ax.scatter(c['wall_seconds'],error,color=colors[variant],s=65,label=variant)
        ax.annotate(variant,(c['wall_seconds'],error),xytext=(5,-14) if variant=='radiation' else (5,5),textcoords='offset points',fontsize=8)
    ax.set(xlabel='Observed local wall time (seconds)',ylabel='Wake velocity RMSE (m/s)' if mode=='flow' else 'Surface maximum temperature RMSE (°C)',title=mode.capitalize()+' versus uniform 0.125 m comparator')
    ax.grid(alpha=.2)
for index,mode in enumerate(['flow','fire']):
    c=next(x for x in d['comparisons'] if x['case']==mode+'_medium' and x['repeat']==1)
    bottom=0
    for routine in ['RADI','FIRE','PRES','DIVG','MASS','VELO','WALL','DUMP']:
        v=c['profile_percent'].get(routine,0)
        axs[2].bar(mode,v,bottom=bottom,label=routine if index==0 else None,color=plt.get_cmap('tab10')(['RADI','FIRE','PRES','DIVG','MASS','VELO','WALL','DUMP'].index(routine)));bottom+=v
axs[2].set(ylabel='FDS reported routine time (%)',title='Medium-grid work breakdown');axs[2].legend(fontsize=8,ncol=2)
fig.suptitle('Mechanism screening: transient 8-second windows; local timings affected by competing workload',fontsize=12)
fig.savefig(ROOT/'results/profiling.png',dpi=150)
