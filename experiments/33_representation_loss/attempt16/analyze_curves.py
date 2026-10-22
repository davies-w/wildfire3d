"""Fixed-panel checkpoint trajectories; late slopes are descriptive, not proof of saturation."""
from pathlib import Path
import json,statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;rep=json.loads((R/'data/collected/report.json').read_text());rows=rep['rows'];plan=rep['plan'];out=R/'data/visuals';out.mkdir(parents=True,exist_ok=True)
keys=['truth_hot_temperature_relative_L1_percent','HRR_curve_relative_L1_percent','radiation_dose_relative_L1_percent','temperature_rise_relative_L1_percent','velocity_vector_relative_L1_percent','temperature_MAE_C']
summary=[]
for item in plan['models']:
 for split in ['train','validation']:
  rr=[r for r in rows if (r['arm'],r['step'],r['split'])==(item['arm'],item['step'],split)]
  assert len(rr)==(12 if split=='train' else 40)
  for window in ['all','post_source','late']:
   configs=[]
   for name in sorted({r['configuration'] for r in rr}):
    ss=[r for r in rr if r['configuration']==name];m={k:statistics.mean(r[window][k] for r in ss if r[window][k] is not None) for k in keys};m['fixed_history_objective']=statistics.mean(r['fixed_history_objective'] for r in ss);m['truth_mean_HRR_kW']=statistics.mean(r[window]['truth_mean_HRR_kW'] for r in ss);configs.append(m)
   for lo,hi in [(0,None),(0,10),(100,None)]:
    gg=[m for m in configs if lo<=m['truth_mean_HRR_kW'] and (hi is None or m['truth_mean_HRR_kW']<hi)]
    summary.append(dict(arm=item['arm'],step=item['step'],expected_sampling_passes=item['step']/item['training_configurations'],split=split,window=window,strength_range=[lo,hi],configurations=len(gg),mean={k:statistics.mean(m[k] for m in gg) if gg else None for k in keys+['fixed_history_objective']},median={k:statistics.median(m[k] for m in gg) if gg else None for k in keys+['fixed_history_objective']}))
late=[]
for arm in sorted({m['arm'] for m in plan['models']}):
 for split in ['train','validation']:
  points=sorted([x for x in summary if x['arm']==arm and x['split']==split and x['window']=='post_source' and x['strength_range']==[0,None]],key=lambda x:x['step'])[-5:]
  late.append(dict(arm=arm,split=split,steps=[p['step'] for p in points],delta_over_last_2000={k:points[-1]['median'][k]-points[0]['median'][k] for k in keys},slope_per_1000_updates={k:float(np.polyfit([p['step']/1000 for p in points],[p['median'][k] for p in points],1)[0]) for k in keys}))
(R/'results/curves.json').write_text(json.dumps(dict(scope=plan['scope'],summary=summary,late_trends=late,interpretation='Descriptive five-checkpoint late slopes. Fixed training panel is not full training set. More steps only establish convergence under the chosen loss/sampling/learning rate; high plateau does not prove an architectural limit.'),indent=2)+'\n')
labels=['Hot temperature error (%)','Heat-release error (%)','Radiation-dose error (%)']
for arm in sorted({m['arm'] for m in plan['models']}):
 fig,axes=plt.subplots(1,4,figsize=(16,4),layout='constrained')
 for split,label in [('train','Training panel (12 configs)'),('validation','Validation (32 configs)')]:
  points=sorted([x for x in summary if x['arm']==arm and x['split']==split and x['window']=='post_source' and x['strength_range']==[0,None]],key=lambda x:x['step'])
  for ax,k,title in zip(axes,keys[:3]+['fixed_history_objective'],labels+['Fixed-history objective (mean)']):
   stat='mean' if k=='fixed_history_objective' else 'median';ax.plot([x['step'] for x in points],[x[stat][k] for x in points],'.-',label=label);ax.set(xlabel='Additional optimizer updates',ylabel=title);ax.grid(alpha=.2)
 axes[0].legend(fontsize=8);fig.suptitle(arm+': every saved 500-step checkpoint; same cases and complete histories');fig.savefig(out/(arm+'-curves.png'),dpi=150);plt.close(fig)
print(json.dumps(late,indent=2))
