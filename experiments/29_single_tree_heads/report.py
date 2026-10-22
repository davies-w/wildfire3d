import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;names=['previous','bound_only','bounded','strength_only','heads','interpolation'];reports={n:json.loads((R/f'results/{n}-evaluation.json').read_text()) for n in names}
summary={n:r['summary'] for n,r in reports.items()};(R/'results/comparison.json').write_text(json.dumps(summary,indent=2))
fig,axes=plt.subplots(2,3,figsize=(14,7),layout='constrained');val=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='validation']
for ax,c in zip(axes.flat,val):
 for n in ['previous','bounded','heads','interpolation']:
  h=next(h for h in reports[n]['histories'] if h['case']==c['case'])
  if n=='previous':ax.plot(h['time_s'],h['truth_HRR_kW'],label='FDS',color='black')
  ax.plot(h['time_s'],h['predicted_HRR_kW'],label=n)
 ax.set_title(f"Validation {c['case'].split('_')[-1]}: {c['wind_speed']:.2f}m/s, {c['angle_deg']:.1f}°");ax.set_yscale('symlog',linthresh=.01);ax.set_ylim(bottom=0);ax.set_xlabel('Seconds');ax.set_ylabel('Total heat release (kW)');ax.axvline(20,color='grey',ls=':');ax.legend(fontsize=7)
fig.suptitle('All six development-validation heat histories — not fresh tests');fig.savefig(R/'results/visuals/validation-heat-histories.png',dpi=140);plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
for ax,(key,label) in zip(axes,[('hot_MAE_C','Hot-region temperature MAE (°C)'),('HRR_curve_relative_L1','Heat-history relative error'),('radiation_dose_relative_L1','Radiation-intensity dose error')]):
 x=np.arange(len(names));train=[summary[n].get('train',{}).get('post_source',{}).get(key,np.nan) for n in names];valid=[summary[n]['validation']['post_source'][key] for n in names];ax.bar(x-.18,train,.36,label='Training');ax.bar(x+.18,valid,.36,label='Validation');ax.set_xticks(x,names,rotation=25);ax.set_title(label);ax.legend()
fig.suptitle('Complete post-source histories (22–180s), averaged by configuration');fig.savefig(R/'results/visuals/comparison.png',dpi=140);plt.close(fig)
for n in names:print(n,json.dumps(summary[n]['validation']['post_source']))
