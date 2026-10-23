"""Plot every available epoch, retaining partial-run status and per-case physical gates."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/visuals';out.mkdir(exist_ok=True);plan=json.loads((R/'coverage-plan.json').read_text());summary=[]
keys=[('objective_MSE','Region-balanced encoded MSE'),('hot_temperature_MAE_C','Hot-region temperature MAE (C)'),('burning_HRR_MAE_kWm3','Burning-region HRR MAE (kW/m3)'),('total_HRR_relative_L1_percent','Total-HRR relative L1 (%)'),('hot_f1','HOT F1'),('total_HRR_MAE_kW','Total-HRR MAE (kW)')]
fig,axs=plt.subplots(2,6,figsize=(24,8))
for row,arm in enumerate(plan['arms']):
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))];assert records and len({r['epoch'] for r in records})==len(records)
 for ax,(key,label) in zip(axs[row],keys):
  for split,style in [('train','--'),('validation','-')]:
   ax.plot([r['epoch'] for r in records],[r['summary'][split]['post_source'][key] for r in records],style,label=split)
  ax.set(title=arm+': '+label,xlabel='Complete epochs');ax.grid(alpha=.2)
  if key=='objective_MSE':ax.set_yscale('log')
  if key=='hot_f1':ax.set_ylim(-.02,1.02)
 report=R/'data/collected'/(arm+'-report.json');rr=json.loads(report.read_text()) if report.exists() else {};summary.append(dict(arm=arm,epochs=records[-1]['epoch'],reason=rr.get('reason','incomplete_not_converged'),selected_epoch=rr.get('selected_epoch'),final=records[-1]['summary'],selected=rr.get('selected'),final_fit_gate=rr.get('final_fit_gate'),selected_fit_gate=rr.get('fit_gate')))
axs[0,0].legend();fig.suptitle('Fixed U-Net continuous-field fitting: post-source training dashed / development-validation solid');fig.tight_layout();fig.savefig(out/'physical-learning-curves.png',dpi=140)
fig,axs=plt.subplots(2,6,figsize=(24,8))
for row,arm in enumerate(plan['arms']):
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))]
 for j,ax in enumerate(axs[row]):
  for split,style in [('train','--'),('validation','-')]:ax.plot([r['epoch'] for r in records],[r['summary'][split]['post_source']['channel_physical_MAE'][j] for r in records],style,label=split)
  ax.set(title=arm+': '+['T C','HRR kW/m3','u m/s','v m/s','w m/s','radiation kW/m2'][j],xlabel='Epoch');ax.grid(alpha=.2)
fig.suptitle('Whole-volume physical MAE, shown separately from burning-region errors');fig.tight_layout();fig.savefig(out/'channel-learning-curves.png',dpi=140)
(R/'results/analysis.json').write_text(json.dumps(dict(arms=summary,scope=plan['scope'],note='Final training fit and validation-selected checkpoint are distinct questions. Epoch/deadline limits do not prove convergence; no expansion without passing physical fitting checks.'),indent=2)+'\n')

# Match the baseline to each arm's actual training cases; never compare single to TRAIN8.
base=json.loads((R/'data/collected/background_baseline-epoch-000.json').read_text())
from metrics import aggregate
fig,axs=plt.subplots(2,4,figsize=(17,8))
for row,arm in enumerate(plan['arms']):
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))]
 cases=base['case_metrics'];windows=[c['windows'] for c in cases]
 ids=[i for i,c in enumerate(cases) if c['split']=='train' and (arm=='eight' or c['case']==plan['single_case'])]
 matched={'train':aggregate(windows,cases,ids),'validation':base['summary']['validation']}
 for ax,key,label in zip(axs[row],['objective_MSE','hot_temperature_MAE_C','burning_HRR_MAE_kWm3','total_HRR_MAE_kW'],['Region-balanced MSE','Hot-region MAE (C)','Burning-region HRR MAE (kW/m3)','Total gas-HRR MAE (kW)']):
  for split,color in [('train','tab:blue'),('validation','tab:orange')]:
   ax.plot([r['epoch'] for r in records],[r['summary'][split]['post_source'][key] for r in records],color=color,label=split)
   ax.axhline(matched[split]['post_source'][key],color=color,linestyle=':',label=split+' background baseline')
  ax.set(title=arm+': '+label,xlabel='Epoch');ax.grid(alpha=.2)
axs[0,0].legend(fontsize=7);fig.suptitle('Post-source model versus matched constant-background baseline');fig.tight_layout();fig.savefig(out/'baseline-learning-curves.png',dpi=140);plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(13,8))
for row,arm in enumerate(plan['arms']):
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))]
 for ax,split in zip(axs[row],['train','validation']):
  for window,color in [('all','tab:blue'),('post_source','tab:orange')]:
   ax.plot([r['epoch'] for r in records],[r['summary'][split][window]['energy_pred_kJ']/1000 for r in records],color=color,label=window+' predicted')
   ax.axhline(records[0]['summary'][split][window]['energy_truth_kJ']/1000,color=color,linestyle=':',label=window+' truth')
  ax.set(title=arm+': '+split,xlabel='Epoch',ylabel='Configuration-mean gas energy (MJ)');ax.grid(alpha=.2)
axs[0,0].legend(fontsize=8);fig.suptitle('Energy integrated from saved gas HRRPUV; separate from global solid oxidation');fig.tight_layout();fig.savefig(out/'energy-learning-curves.png',dpi=140);plt.close(fig)
