"""Static scientific summary of measured CPU cost, profiles, and thermal deviation."""
import json,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'results/analysis.json').read_text());runs=[r for r in d['runs'] if r['case'] not in ('smoke','lot_full')]
profiles=[json.loads(p.read_text()) for p in sorted((ROOT/'results/profiles').glob('symbolized-*.json')) if 'smoke' not in p.name]
fig,axs=plt.subplots(2,2,figsize=(13,9),layout='constrained')
ax=axs[0,0]
if runs:
 ax.barh([r['case'] for r in runs],[r['cpu_total_s']/60 for r in runs],color='#267e97');ax.set(xlabel='Measured process CPU-minutes',title='Equal 30-second simulated exposures');ax.axvline(5,color='#b33b38',ls='--',label='Five CPU-minute target');ax.legend()
colors={'FDS':'#267e97','OpenMP runtime':'#cc8a39','Other libraries':'#888888'}
for p in profiles:
 values={k:0 for k in colors}
 for m in p['modules']:
  key='FDS' if m['name']=='FDS' else 'OpenMP runtime' if 'libgomp' in m['name'] else 'Other libraries';values[key]+=m['percent_all_cpu_samples']
 left=0
 for key,v in values.items():axs[0,1].barh(p['case'],v,left=left,color=colors[key],label=key if p is profiles[0] else None);left+=v
axs[0,1].set(xlabel='Exclusive CPU samples (%)',title='Where CPU samples land',xlim=(0,100))
if profiles:axs[0,1].legend(loc='lower right')
for case,color in [('hot_a','#267e97'),('hot_passive','#57924c'),('hot_radiation','#cc8a39'),('hot_coarse','#b33b38')]:
 p=ROOT/'data/cloud'/case/(case+'_devc.csv')
 if not p.exists():continue
 with p.open() as f:
  r=csv.reader(f);next(r);keys=[v.strip().strip('"') for v in next(r)];rows=[dict(zip(keys,map(float,v))) for v in r if v]
 axs[1,0].plot([r['Time'] for r in rows],[r['house_wall_max'] for r in rows],label=case,color=color,ls='--' if case=='hot_passive' else '-')
axs[1,0].axhline(350,color='gray',ls=':',label='Wall ignition threshold');axs[1,0].set(xlabel='Simulated seconds',ylabel='Maximum wall device temperature (C)',title='Coarsening changes the ignition prediction');axs[1,0].legend(fontsize=8)
full=next((r for r in d['runs'] if r['case']=='lot_full'),None)
if full:
 curve=full['prefix_cost'];axs[1,1].plot([v['simulated_s'] for v in curve],[v['cpu_s']/60 for v in curve],color='#267e97');axs[1,1].axhline(5,color='#b33b38',ls='--');axs[1,1].set(xlabel='Simulated seconds',ylabel='Accumulated process CPU-minutes',title=f"Long baseline: {full.get('last_step_time_s',full['physical_seconds_reached']):g}/600 s"+(' (partial)' if not full['full_horizon'] else ''))
else:
 axs[1,1].axis('off');axs[1,1].text(.05,.7,'Long baseline still running.\nNo full-horizon claim yet.',transform=axs[1,1].transAxes)
fig.savefig(ROOT/'results/profiling.png',dpi=160)
