from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;report=json.loads((R/'data/collected/report.json').read_text());v=R/'data/visuals';v.mkdir(exist_ok=True)
for feature,label in [(None,'normalized rollout MSE'),(0,'Water MAE (kg)'),(1,'Dry fuel MAE (kg)'),(2,'Fuel-gas release MAE (kg/s)')]:
 fig,axes=plt.subplots(2,5,figsize=(20,8))
 for ax,fold in zip(axes.flat,report['folds']):
  for split in ['train','validation']:
   h=fold['history'];ys=[r[split]['rollout'].get('objective',np.nan) if feature is None else (r[split]['rollout'].get('physical_MAE_by_feature') or [np.nan]*3)[feature] for r in h];ax.plot([r['epoch'] for r in h],ys,label=split)
  ax.axvline(fold['selected_epoch'],ls=':',color='black');ax.set_title(f"Fold {fold['fold']} · {fold['stop_reason']}");ax.set_xlabel('Epoch');ax.set_ylabel(label);ax.legend()
 fig.suptitle('Three-state model: training vs validation; dotted line is selected epoch');fig.tight_layout();fig.savefig(v/f'curves-{feature}.png',dpi=140);plt.close(fig)
summary=dict(folds=[{k:f[k] for k in ['fold','epochs','selected_epoch','stop_reason']} for f in report['folds']],tests=report['tests'],scope=report['scope']);(R/'results/analysis.json').write_text(json.dumps(summary,indent=2))

# Supplemental views retain early instability while revealing subsequent learning.
for feature,label in [(None,'Normalized rollout MSE'),(0,'Water MAE (kg)'),(1,'Dry fuel MAE (kg)'),(2,'Fuel-gas release MAE (kg/s)')]:
 for view in ['log','after-warmup']:
  fig,axes=plt.subplots(2,5,figsize=(20,8))
  for ax,fold in zip(axes.flat,report['folds']):
   for split in ['train','validation']:
    h=[r for r in fold['history'] if view=='log' or r['epoch']>=21]
    y=[r[split]['rollout']['objective'] if feature is None else (r[split]['rollout'].get('physical_MAE_by_feature') or [np.nan]*3)[feature] for r in h]
    ax.plot([r['epoch'] for r in h],y,label=split)
   if view=='log':ax.set_yscale('log')
   ax.axvline(fold['selected_epoch'],ls=':',color='black');ax.set_title(f"Fold {fold['fold']} · selected {fold['selected_epoch']}");ax.set_xlabel('Epoch');ax.set_ylabel(label);ax.legend()
  fig.suptitle(f'{view}: all values retained within shown epoch range; selected epoch dotted');fig.tight_layout();fig.savefig(v/f'curves-{feature}-{view}.png',dpi=140);plt.close(fig)
# Each held-out fold has 48 physical configurations; worker metrics average replicas
# within configuration before averaging configurations. Window means are fold means.
aggregate={}
for mode in ['one_step','rollout']:
 rows=[t['metrics'][mode] for t in report['tests']]
 aggregate[mode]={k:np.mean([r[k] for r in rows],axis=0).tolist() for k in ['objective','physical_MAE_by_feature','negative_fraction_by_feature','negative_magnitude_mean_by_feature','mass_increase_fraction','mass_increase_total_kg','released_fuel_integral_MAE_kg','peak_release_MAE_kg_s','peak_time_MAE_s']}
 aggregate[mode]['global_minimum_by_feature']=np.min([r['minimum_by_feature'] for r in rows],axis=0).tolist()
 aggregate[mode]['window_fold_mean_MAE']={w:np.mean([r['physical_MAE_by_window'][w] for r in rows],axis=0).tolist() for w in rows[0]['physical_MAE_by_window']}
aggregate['persistence_rollout_objective_mean']=float(np.mean([t['persistence']['rollout']['objective'] for t in report['tests']]))
aggregate['scope']='Equal configuration averages across ten disjoint 48-configuration test folds; active/quiet window results are means of fold conditional means. Negative magnitude averages include nonnegative predictions as zero. Minima are global. Formerly examined data, reshuffled with authorization.'
summary['aggregate']=aggregate
(R/'results/analysis.json').write_text(json.dumps(summary,indent=2))
