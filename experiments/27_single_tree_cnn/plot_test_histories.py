"""All six untouched cases: scalar histories from full FDS/CNN/baseline fields."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent
f=json.loads((R/'results/prediction-freeze.json').read_text())
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
cases=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='test']
fig,axes=plt.subplots(6,3,figsize=(13,15),sharex=True)
for row,c in enumerate(cases):
 t=np.load(R/'data/fields'/f"{c['case']}-time.npy");a=np.load(R/'data/fields'/f"{c['case']}.npy",mmap_mode='r')
 target=np.arange(0,181,2);ix=abs(t[:,None]-target).argmin(0)
 arrays=[('FDS',np.array(a[ix]),'#111827'),('CNN · 32 training',np.load(R/'data/predictions'/f"cnn_32_{c['case']}.npy",mmap_mode='r'),'#d97706'),('Interpolation · 32',np.load(R/'data/predictions'/f"interpolation_32_{c['case']}.npy",mmap_mode='r'),'#2563eb')]
 for label,v,color in arrays:
  # Volume-integrated heat release, hot volume, and spatial maximum gas temperature.
  ys=[np.maximum(v[:,1],0).sum(axis=(1,2,3))*.125/1000,(v[:,0]>100).sum(axis=(1,2,3))*.125,v[:,0].max(axis=(1,2,3))]
  for col,y in enumerate(ys):axes[row,col].plot(target,y,label=label,color=color,lw=1.5)
 for ax in axes[row]:ax.axvspan(0,20,color='grey',alpha=.13);ax.grid(alpha=.18);ax.set_xlim(0,180)
 axes[row,0].set_ylabel(f"Test {row} · {c['wind_speed']:.2f} m/s\n{c['angle_deg']:.0f}° ignition\nMW")
 axes[row,1].set_ylabel('m³');axes[row,2].set_ylabel('°C')
for ax,title in zip(axes[0],['Heat release within domain','Gas volume above 100°C','Peak gas temperature']):ax.set_title(title)
for ax in axes[-1]:ax.set_xlabel('Physical time (s)')
axes[0,0].legend(fontsize=8)
fig.suptitle('Untouched conditions: same fields, same clock\nGrey: artificial ignition active. Fixed generic 10m-top canopy; no embers.',fontsize=13)
fig.tight_layout(rect=[0,0,.99,.95]);p=R/'results/visuals/test-histories.png';fig.savefig(p,dpi=150);plt.close(fig);print(p)
