"""Show recorded samples and evaluation endpoints without implying measured learning curves."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];out=R/'diagnostics';report=json.loads((R/'attempt14/data/collected/report.json').read_text());summary=json.loads((R/'attempt14/results/coverage-summary.json').read_text())['summary']
fig,axs=plt.subplots(1,3,figsize=(14,4.6),layout='constrained')
for arm,label in [('continue120','120 configurations'),('expand360','360 configurations')]:
 h=report['training'][arm]['history'];axs[0].plot([x['step'] for x in h],[x['loss'] for x in h],'.-',label=label,alpha=.8)
axs[0].set(yscale='log',xlabel='Additional optimizer updates',ylabel='Single sampled-window objective (log scale)',title='Recorded training loss samples\nDifferent cases/times; NOT average loss');axs[0].legend(fontsize=8)
keys=[('truth_hot_temperature_relative_L1_percent','Hot temperature'),('HRR_curve_relative_L1_percent','Heat release'),('radiation_dose_relative_L1_percent','Radiation dose')]
for ax,(arm,label) in zip(axs[1:],[('continue120','120 configurations'),('expand360','360 configurations')]):
 for key,name in keys:
  values=[next(x for x in summary if x['arm']==arm and x['stage']==s and x['cohort']=='validation32' and x['window']=='post_source')['median'][key] for s in ['initial','final']]
  ax.plot([0,12000],values,'o--',label=name)
  for step,val in zip([0,12000],values):ax.annotate(f'{val:.1f}%',(step,val),xytext=(4,4),textcoords='offset points',fontsize=8)
 ax.set(xlabel='Additional optimizer updates',ylabel='Validation median relative error (%)',title=f'{label}: evaluation endpoints\nNo measurements between endpoints',xlim=(-1500,14500),ylim=(35,90),xticks=[0,12000]);ax.legend(fontsize=8)
fig.suptitle('Attempt14: available evidence cannot establish a learning plateau',fontsize=14)
fig.savefig(out/'learning-evidence.png',dpi=150)
for arm in ['continue120','expand360']:
 for cohort in ['reference_train120','validation32']:
  for stage in ['initial','final']:
   x=next(x for x in summary if x['arm']==arm and x['stage']==stage and x['cohort']==cohort and x['window']=='post_source');print(arm,cohort,stage,{k:round(x['median'][k],2) for k,_ in keys})
