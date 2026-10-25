"""Analyze saved forecasts only; never fits or chooses a winning size."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;report=json.loads((R/'data/collected/report.json').read_text());schema=json.loads((R/'schema.json').read_text());out={'scope':'One fixed held-out split; eight nested training sizes. Not averaged over ten test folds. Frozen scorecard-v1.','sizes':[]}
assert report['success'] and len(report['tests'])==8
assert len({x['initial_hash'] for x in report['folds']})==1
names=['Water','Dry fuel','Fuel-gas release','Surface-heating index']
for test,train,split in zip(report['tests'],report['folds'],schema['rotations']):
 row=dict(training_folds=test['training_fold_count'],training_configurations=48*test['training_fold_count'],training_histories=len(split['train']),epochs=train['epochs'],selected_epoch=train['selected_epoch'],stop_reason=train['stop_reason'],optimizer_updates=train['history'][-1]['optimizer_updates'],horizons={},rollout=test['metrics']['rollout'])
 for h,metric in test['horizons'].items():
  row['horizons'][str(int(h)*2)]={}
  for phase in ['v1_active','v1_quiet','v1_weak','v1_transition']:
   m,b,t=[metric[key][phase] for key in ['model_windows','no_change_windows','truth_windows']]
   if m is None or b is None or t is None:row['horizons'][str(int(h)*2)][phase]=None;continue
   row['horizons'][str(int(h)*2)][phase]=dict(MAE=m,no_change_MAE=b,mean_absolute_truth=t,error_vs_sim_percent=[100*x/y if y else None for x,y in zip(m,t)],improvement_vs_no_change_percent=[100*(1-x/y) if y else None for x,y in zip(m,b)])
 out['sizes'].append(row)
D=R/'data/learning_curve';D.mkdir(exist_ok=True)
for phase in ['v1_active','v1_quiet','v1_weak','v1_transition']:
 fig,axes=plt.subplots(2,4,figsize=(16,7),sharex=True)
 for f,name in enumerate(names):
  for j,key in enumerate(['error_vs_sim_percent','improvement_vs_no_change_percent']):
   y=[(r['horizons']['16'][phase] or {}).get(key,[None]*4)[f] for r in out['sizes']]
   axes[j,f].plot(range(1,9),[np.nan if v is None else v for v in y],marker='o',color='#1878c8');axes[j,f].set_title(name);axes[j,f].set_xticks(range(1,9));axes[j,f].set_xlabel('Training folds');axes[j,f].axhline(0,color='#aaaaaa',lw=.7)
  axes[0,0].set_ylabel('Error vs simulation (%) — lower better');axes[1,0].set_ylabel('Improvement vs no change (%) — higher better')
 fig.suptitle('16 seconds ahead · '+phase.removeprefix('v1_')+' · fixed test fold');fig.tight_layout();fig.savefig(D/(phase+'.png'),dpi=150);plt.close(fig)
(R/'results/learning-curve.json').write_text(json.dumps(out,indent=2,allow_nan=False))
html=['<html><meta charset="utf-8"><title>Training-data learning curve</title><body style="font:16px system-ui;max-width:1200px;margin:30px auto"><h1>Does more training data help?</h1><p>Plain four-state GRU. One fixed validation/test split; fresh identical initial weights for each nested training size. No gates or physical constraints. Each fold adds 48 configurations. Single split/order: not ten-fold uncertainty. More data also gives more optimizer updates per epoch. Heating is an index, not energy; fuel gas is not heat release. Previously examined simulations, not physical validation.</p>']
for phase in ['v1_active','v1_quiet','v1_weak','v1_transition']:html.append('<img style="width:100%" src="'+phase+'.png">')
html.append('<h2>Training completeness</h2><table><tr><th>Folds</th><th>Histories</th><th>Epochs</th><th>Selected</th><th>Updates</th><th>Stop reason</th></tr>')
for r in out['sizes']:html.append('<tr>'+''.join('<td style="padding:8px">'+str(r[k])+'</td>' for k in ['training_folds','training_histories','epochs','selected_epoch','optimizer_updates','stop_reason'])+'</tr>')
html.append('</table></body></html>');(D/'report.html').write_text(''.join(html));print('Saved learning-curve report')
