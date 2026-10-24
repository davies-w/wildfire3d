"""Configuration-balanced held-out fold reporting, curves and failure flags."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'data/collected';out=R/'data/visuals';out.mkdir(exist_ok=True)
r=json.loads((D/'report.json').read_text());schema=json.loads((R/'schema.json').read_text());assert len(r['folds'])==len(r['tests'])==10
fig,axs=plt.subplots(2,5,figsize=(22,8));summary=[]
for ax,fold,test in zip(axs.flat,r['folds'],r['tests']):
 h=fold['history'];ep=[v['epoch'] for v in h]
 for split,color in [('train','#1779a8'),('validation','#d67324')]:
  ax.plot(ep,[v[split]['rollout']['objective'] for v in h],label=split,color=color)
 ax.axvline(fold['selected_epoch'],ls='--',color='black',lw=.8);ax.set(title=f"Fold{fold['fold']} | {fold['stop_reason']}",xlabel='epoch',ylabel='Autonomous rollout normalized MSE');ax.set_yscale('symlog',linthresh=.001);ax.grid(alpha=.2);ax.legend(fontsize=8)
 summary.append(dict(fold=fold['fold'],epochs=fold['epochs'],selected_epoch=fold['selected_epoch'],stop_reason=fold['stop_reason'],test_rollout_objective=test['metrics']['rollout']['objective'],persistence_rollout_objective=test['persistence']['rollout']['objective'],test_one_step_objective=test['metrics']['one_step']['objective'],negative_gas_HRR_fraction=test['metrics']['rollout']['negative_gas_HRR_fraction'],invalid_active_covariance_fraction=test['metrics']['rollout']['invalid_active_covariance_fraction']))
fig.tight_layout();fig.savefig(out/'ten-fold-learning-curves.png',dpi=150);plt.close(fig)
for feature_index,name in enumerate(schema['state_names']):
 fig,axs=plt.subplots(2,5,figsize=(20,7))
 for ax,fold in zip(axs.flat,r['folds']):
  h=fold['history']
  for split,color in [('train','#1779a8'),('validation','#d67324')]:
   vals=[v[split]['rollout'].get('physical_MAE_by_feature') for v in h];ax.plot([v['epoch'] for v in h],[x[feature_index] if x is not None else np.nan for x in vals],label=split,color=color)
  ax.axvline(fold['selected_epoch'],ls='--',color='black',lw=.7);ax.set(title=f"Fold{fold['fold']}",xlabel='epoch');ax.grid(alpha=.2)
 fig.suptitle(name+' | autonomous rollout MAE in recorded physical units');axs.flat[0].legend();fig.tight_layout();fig.savefig(out/f'feature-{feature_index:02}.png',dpi=110);plt.close(fig)
rows=[row for t in r['tests'] for row in t['metrics']['rollout']['cases']];assert len(rows)==520 and len({v['case'] for v in rows})==520
groups={}
for v in rows:groups.setdefault(v['configuration'],[]).append(v)
assert len(groups)==480
mae=[];obj=[]
for rs in groups.values():
 if any(v['physical_MAE_by_feature'] is None or v['objective'] is None for v in rs):continue
 mae.append(np.mean([v['physical_MAE_by_feature'] for v in rs],axis=0));obj.append(np.mean([v['objective'] for v in rs]))
proof=dict(complete=True,histories=520,configurations=480,finite_configurations=len(mae),pooled_configuration_mean_rollout_objective=float(np.mean(obj)) if len(obj)==480 else None,physical_MAE_by_feature={n:float(v) for n,v in zip(schema['state_names'],np.mean(mae,axis=0))} if len(mae)==480 else None,folds=summary,scope='New grouped cross-validation on previously examined simulations. No physical validation; no proven Markov sufficiency or conservation. Epoch caps are not convergence. Invalid predictions reported without silent clipping.')
(R/'results/analysis.json').write_text(json.dumps(proof,indent=2,allow_nan=False));print(json.dumps({k:v for k,v in proof.items() if k!='physical_MAE_by_feature'},indent=2))
