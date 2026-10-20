import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;tests=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='test'];fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for ax,c in zip(axes.flat,tests):
 name=c['case'];t=np.load(R/f'data/test-fields/{name}-time.npy');a=np.load(R/f'data/test-fields/{name}.npy',mmap_mode='r');ax.plot(t,a[:,1].sum((1,2,3))*.125,label='FDS',color='black')
 for model,label in [('original','Original CNN'),('physical','Repaired CNN'),('interpolation','Interpolation')]:
  p=np.load(R/f'data/predictions/{model}_{name}.npy',mmap_mode='r');ax.plot(np.arange(0,181,2),p[:,1].sum((1,2,3))*.125,label=label)
 ax.set_yscale('symlog',linthresh=.01);ax.set_ylim(bottom=0);ax.set_xlabel('Time (s)');ax.set_ylabel('Total heat release (kW)');ax.set_title(f'{name}: {c["wind_speed"]:.2f}m/s, {c["angle_deg"]:.1f}°');ax.axvline(20,color='grey',ls=':');ax.legend(fontsize=8)
fig.suptitle('Six fresh tests: total heat release, including weak residual values\nSource stops at20s; same fixed generic crown, no embers');fig.savefig(R/'results/visuals/heat-histories.png',dpi=140)
