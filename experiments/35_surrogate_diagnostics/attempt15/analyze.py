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
