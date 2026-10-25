"""Actual endpoint values at 16 steps for one fixed test case; no fitting."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'data/scenario_values';D.mkdir(exist_ok=True)
a=np.load(R/'data/sequences.npz');m=json.loads((R/'schema.json').read_text());one=np.load(R/'data/collected/fold01-horizon01-predictions.npz');sixteen=np.load(R/'data/collected/fold01-horizon16-predictions.npz')
i=int(m['rotations'][0]['test'][0]);j=int(np.flatnonzero(one['case_indices']==i)[0]);k=int(np.flatnonzero(sixteen['case_indices']==i)[0]);s=a['state'][i];t=a['time'][i];n=75
hz=np.load(R/'data/scenario_horizons/predictions.npz');targets=np.arange(1,91);steps=np.minimum(targets,16);origins=targets-steps;plot_time=t[targets]
values={'Simulation':s[targets],'No change':s[origins],'First predicted change × steps':s[origins]+steps[:,None]*(hz['1'][origins]-s[origins]),'Recursive model':np.stack([hz[str(h)][o] for h,o in zip(steps,origins)])}
assert all(x.shape==(90,4) for x in values.values());assert i in m['rotations'][0]['test']
fig,axs=plt.subplots(2,2,figsize=(15,9),sharex=True)
styles=[dict(color='#159447',lw=.8,ls='-'),dict(color='#9854bc',lw=.8,ls='-'),dict(color='#e67e13',lw=.8,ls='-'),dict(color='#1878c8',lw=.8,ls='-')]
for f,(ax,title,unit) in enumerate(zip(axs.flat,['Water','Dry fuel','Fuel-gas release','Surface-heating index'],['kg','kg','kg/s','K'])):
 for (label,v),style in zip(values.items(),styles):ax.plot(plot_time,v[:,f],label=label,**style)
 ax.set_title(title,fontsize=16,loc='left');ax.set_ylabel(unit);ax.set_xlabel('Target simulation time (s)');ax.grid(False);ax.set_xlim(0,180);ax.set_yscale('symlog',linthresh=[.001,.01,.00001,.1][f])
 for spine in ax.spines.values():spine.set_visible(False)
fig.suptitle(f"{m['cases'][i]['case']} · gated four-state GRU · Growing to 16 steps, then rolling 32-second horizon",fontsize=19,y=.985)
handles,labels=axs.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.947),ncol=4,frameon=False,fontsize=11)
fig.text(.5,.025,'90 targets: horizon grows from 1 to 16 steps, then stays at 16 steps (32 seconds).\nOrange extends the first predicted physical change linearly; blue recomputes each step using its own predictions. No clipping.',ha='center',fontsize=11)
fig.tight_layout(rect=(0,.075,1,.90));fig.savefig(D/'four-state-values.png',dpi=160);plt.close(fig)
np.savez_compressed(D/'values.npz',origin_time=t[origins],target_time=plot_time,horizon_steps=steps,**{str(z):v for z,v in enumerate(values.values())})
(D/'metadata.json').write_text(json.dumps(dict(case=m['cases'][i],fold=1,model='gated',steps=16,seconds=32,selection='First test case in rotation0, fixed without inspecting outcomes',series=list(values),note='Gas release is not heat output; surface-heating index is not stored energy. Saved GPU predictions; no new inference/training.'),indent=2))
(D/'report.html').write_text((R/'scenario_chart.html').read_text().replace('__DATA__',json.dumps(dict(time=plot_time.tolist(),values=[v.tolist() for v in values.values()]))))
print(D/'four-state-values.png')
