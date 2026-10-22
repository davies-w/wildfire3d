"""Native wall-cell sampled maxima over0–180s; shared nonlinear scale."""
import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import FuncNorm
ROOT=Path(__file__).parent
cases=json.loads((ROOT/'cases.json').read_text());maps=[]
for c in cases:
 folder=ROOT/'data/cloud'/c['case'];result=json.loads((folder/'result.json').read_text());assert result['full_horizon']
 with (folder/(c['case']+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[k.strip().strip('"') for k in next(r)];rows=np.array([list(map(float,row)) for row in r if row]);d=dict(zip(keys,rows.T))
 assert abs(d['Time'][-1]-180)<1e-5
 ps=[p for p in c['patches'] if p['ior']==-1];a=np.full((round(5/c['dx']),round(6/c['dx'])),np.nan)
 for p in ps:
  x,y,z=p['xyz'];assert x==11
  a[int(z/c['dx']),int((y-8)/c['dx'])]=float(np.max(d[p['id']+'_T']))
 assert np.isfinite(a).all();maps.append((c,a))
lo=20.;hi=max(float(a.max()) for _,a in maps)
norm=FuncNorm((lambda t: np.log1p(np.maximum(t-20.,0)),lambda u:20.+np.expm1(u)),vmin=lo,vmax=hi)
fig,axes=plt.subplots(3,4,figsize=(13,9),constrained_layout=True,sharex=True,sharey=True)
columns=[(False,1),(True,1),(False,.5),(True,.5)]
for c,a in maps:
 row='ABC'.index(c['layout']);col=columns.index((c['expanded'],c['dx']));ax=axes[row,col]
 im=ax.imshow(a,origin='lower',extent=(8,14,0,5),norm=norm,cmap='inferno',interpolation='nearest',aspect='equal')
 if row==0:ax.set_title(('Expanded' if c['expanded'] else 'Compact')+f" · {c['dx']:g} m cells",fontsize=12)
 if col==0:ax.set_ylabel(f"Layout {c['layout']}\nHeight z (m)")
 if row==2:ax.set_xlabel('Along wall y (m)')
 ax.set_xticks([8,10,12,14]);ax.set_yticks([0,1,2,3,4,5]);ax.text(.03,.96,f"{a.min():.1f}–{a.max():.1f} °C",transform=ax.transAxes,va='top',color='white',fontsize=10,bbox=dict(facecolor='black',alpha=.55,pad=2,edgecolor='none'))
ticks=[v for v in [20,20.5,21,22,25,30,40,60,100,150,200,300,500,800] if v<=hi]
cb=fig.colorbar(im,ax=axes,shrink=.8,ticks=ticks,label='Peak temperature (°C) · log(1 + rise above 20°C)')
cb.ax.set_yticklabels([str(v) for v in ticks])
fig.suptitle('West wall · peak temperature per cell over 0–180 s\nShared nonlinear scale emphasizes low-temperature differences',fontsize=15)
out=ROOT/'data/analysis';out.mkdir(exist_ok=True);fig.savefig(out/'peak-west-wall-all-12.png',dpi=180);fig.savefig(out/'peak-west-wall-all-12.pdf');plt.close(fig)
(ROOT/'results/peak-wall-maps.json').write_text(json.dumps(dict(time_window_s=[0,180],sampling_interval_s=1,scale="log1p(T-20C)",face='west x=11m, y8:14m, z0:5m',units='C',shared_scale=[lo,hi],source='Maximum of1-second WALL TEMPERATURE DEVC samples at each native face cell centre; maxima need not occur simultaneously. No smoothing.',cases=[dict(case=c['case'],min_C=float(a.min()),max_C=float(a.max()),mean_C=float(a.mean())) for c,a in maps]),indent=2));print('Shared range',lo,hi)
