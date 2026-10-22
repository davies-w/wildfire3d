"""Analyze completed or partial epoch evidence without training."""
from pathlib import Path
import json,statistics,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/visuals';out.mkdir(exist_ok=True)
plan=json.loads((R/'coverage-plan.json').read_text());cs=json.loads((R/'cases.json').read_text());result={'complete':(R/'data/collected/complete.json').exists(),'arms':{},'scope':plan,'warning':'Budget/epoch limit is not proof of saturation; curves use full arm training set and configuration-balanced validation. Oracle uses true HRR at inference.'}
for arm in ['source','single','eight','oracle']:
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))]
 if not records:continue
 expected={c['case'] for c in cs if c['split']=='validation' or arm!='single' or c['case']==plan['single_case']}
 for r in records:assert {v['case'] for v in r['rows']}==expected
 def mean(rows,fn):
  cfg={}
  for r in rows:
   v=fn(r)
   if v is not None and np.isfinite(v):cfg.setdefault(r['configuration'],[]).append(v)
  return statistics.mean(statistics.mean(v) for v in cfg.values()) if cfg else None
 keys=[('Normalized MAE',lambda r:r['normalized_MAE'])]
 if arm=='source':keys += [('HRR MAE (kW)',lambda r:r['HRR_MAE_kW']),('HRR error (%)',lambda r:r['HRR_relative_L1_percent'])]
 else:keys += [('Hot-temperature error (%)',lambda r:r['post_source']['truth_hot_relative_L1_percent']),('HRR error (%)',lambda r:r['post_source']['HRR_relative_L1_percent']),('Radiation-dose error (%)',lambda r:r['post_source']['radiation_dose_relative_L1_percent']),('Temperature MAE (C)',lambda r:r['post_source']['channel_physical_MAE'][0]),('Velocity X MAE (m/s)',lambda r:r['post_source']['channel_physical_MAE'][2])]
 fig,axs=plt.subplots(2,3,figsize=(15,8));summary=[]
 for ax,(label,fn) in zip(axs.flat,keys):
  for split in ['train','validation']:
   ys=[mean([v for v in r['rows'] if v['split']==split],fn) for r in records];ax.plot([r['epoch'] for r in records],ys,label=split);summary.append(dict(metric=label,split=split,initial=ys[0],final=ys[-1],last_five=ys[-5:]))
  ax.set_title(label);ax.set_xlabel('Complete training epochs');ax.grid(alpha=.25);ax.legend()
 if arm=='source':
  for ax in list(axs.flat)[3:]:ax.set_visible(False)
 fig.suptitle(arm+' — full training histories; 32 development validation configurations\nPhysical metrics use post-source frames for field models; no pristine test');fig.tight_layout();fig.savefig(out/(arm+'-curves.png'),dpi=150);plt.close(fig)
 result['arms'][arm]=dict(epochs_observed=[r['epoch'] for r in records],summary=summary,training_loss=[dict(epoch=r['epoch'],mean=r.get('mean_training_loss')) for r in records],fitting_target_met=summary[0]['final']<=.05)
(R/'results/analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v['summary'][:2] for k,v in result['arms'].items()},indent=2))
