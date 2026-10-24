"""Compare two architectures on fixed grouped folds and forecast horizons."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;r=json.loads((R/'data/collected/report.json').read_text());v=R/'data/visuals';v.mkdir(exist_ok=True)
assert len(r['folds'])==len(r['tests'])==20
summary={'scope':r['scope'],'arms':{},'folds':[{k:f[k] for k in ['kind','rotation','epochs','selected_epoch','stop_reason']} for f in r['folds']]}
for kind in ['scalar','spatial']:
 folds=[f for f in r['folds'] if f['kind']==kind];tests=[f for f in r['tests'] if f['kind']==kind]
 for feature,label in [(None,'Normalized MSE'),(0,'Water MAE kg'),(1,'Dry-fuel MAE kg'),(2,'Fuel-gas release MAE kg/s'),(3,'Surface-heating index MAE K'),(4,'Heating moment X MAE K m'),(5,'Heating moment Y MAE K m'),(6,'Heating moment Z MAE K m')]:
  fig,axes=plt.subplots(2,5,figsize=(20,8))
  for ax,f in zip(axes.flat,folds):
   for split in ['train','validation']:
    h=f['history'];y=[x[split]['rollout'].get('objective',np.nan) if feature is None else (x[split]['rollout'].get('physical_MAE_by_feature') or [np.nan]*3)[feature] for x in h];ax.plot([x['epoch'] for x in h],y,label=split)
   ax.set_yscale('log');ax.axvline(f['selected_epoch'],ls=':',color='black');ax.set_title(f"Fold{f['rotation']} {f['stop_reason']}");ax.set_xlabel('Epoch');ax.set_ylabel(label);ax.legend()
  fig.suptitle(kind+' full autonomous rollouts; log scale; selected epoch dotted');fig.tight_layout();fig.savefig(v/f'{kind}-{feature}.png',dpi=140);plt.close(fig)
 summary['arms'][kind]={'tests':tests,'rollout_MAE_equal_fold_mean':np.mean([x['metrics']['rollout'].get('physical_MAE_by_feature',[np.nan]*3) for x in tests],axis=0).tolist(),'one_step_MAE_equal_fold_mean':np.mean([x['metrics']['one_step'].get('physical_MAE_by_feature',[np.nan]*3) for x in tests],axis=0).tolist()}
fig,axes=plt.subplots(1,3,figsize=(15,4))
for k,label in enumerate(['Water kg','Dry fuel kg','Release kg/s']):
 for kind in ['scalar','spatial']:
  tests=summary['arms'][kind]['tests'];hs=[1,4,8,16,45];ys=[np.mean([t['horizons'][str(h)]['model_MAE'][k] if t['horizons'][str(h)]['finite'] else np.nan for t in tests]) for h in hs];axes[k].plot(np.array(hs)*2,ys,'o-',label=kind)
 hold=[np.mean([t['horizons'][str(h)]['no_change_MAE'][k] for t in tests]) for h in hs];axes[k].plot(np.array(hs)*2,hold,'--',label='No change');axes[k].set_xlabel('Forecast horizon seconds');axes[k].set_ylabel(label);axes[k].legend()
fig.tight_layout();fig.savefig(v/'horizon-errors.png',dpi=150);plt.close(fig)
(R/'results/analysis.json').write_text(json.dumps(summary,indent=2))
