"""Consolidate completed diagnostics; no fitting or model selection."""
from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent; rows=[]
for attempt,arm,epochs in [('attempt03','single',80),('attempt03','eight',20),('attempt03','oracle',20),('attempt04','low',80),('attempt04','restart',80),('attempt05','clamped',80),('attempt05','raw_hrr',80)]:
 d=json.loads((R.parent/attempt/'data/collected'/f'{arm}-epoch-{epochs:03d}.json').read_text())
 rec={'attempt':attempt,'arm':arm,'epochs_in_stage':epochs,'metrics':{}}
 for split in ['train','validation']:
  rr=[r for r in d['rows'] if r['split']==split]; groups={}
  for r in rr:groups.setdefault(r['configuration'],[]).append(r)
  for key,fn in [('common_normalized_MAE',lambda r:r['normalized_MAE']),('post_source_HRR_percent',lambda r:r['post_source']['HRR_relative_L1_percent']),('post_source_hotT_percent',lambda r:r['post_source']['truth_hot_relative_L1_percent']),('post_source_radiation_percent',lambda r:r['post_source']['radiation_dose_relative_L1_percent'])]:
   values={g:statistics.mean(fn(r) for r in rs if fn(r) is not None) for g,rs in groups.items() if any(fn(r) is not None for r in rs)}
   rec['metrics'][split+'/'+key]={'mean':statistics.mean(values.values()),'median':statistics.median(values.values()),'max':max(values.values()),'per_configuration':values}
 rows.append(rec)
(R/'results/final-summary.json').write_text(json.dumps({'rows':rows,'warning':'Development validation, not pristine test. One-case continuations diagnose fitting, not generalization. Oracle receives true HRR. Percentage means are sensitive to weak denominators.'},indent=2))
fig,axes=plt.subplots(1,2,figsize=(12,4.5))
for arm in ['clamped','raw_hrr']:
 records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob(arm+'-epoch-*.json'))]
 for ax,metric in zip(axes,['normalized_MAE','HRR_relative_L1_percent']):
  vals=[]
  for r in records:
   t=next(v for v in r['rows'] if v['split']=='train');vals.append(t[metric] if metric=='normalized_MAE' else t['post_source'][metric])
  ax.plot([r['epoch'] for r in records],vals,label=arm)
for ax,title in zip(axes,['Training: common normalized MAE','Training: post-source total-HRR error (%)']):ax.set_title(title);ax.set_xlabel('Additional complete epochs');ax.grid(alpha=.25);ax.legend()
fig.suptitle('One-trajectory clamp diagnostic — aggregate fit does not establish burning fidelity');fig.tight_layout();fig.savefig(R/'data/final-summary.png',dpi=160)
print(json.dumps({r['arm']:{k:{x:v[x] for x in ['mean','median','max']} for k,v in r['metrics'].items() if 'HRR' in k} for r in rows[-2:]},indent=2))
