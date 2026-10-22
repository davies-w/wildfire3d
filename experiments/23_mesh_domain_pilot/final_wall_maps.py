"""Native wall-cell temperatures at180s; shared scale across all12 cases."""
import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
  a[int(z/c['dx']),int((y-8)/c['dx'])]=d[p['id']+'_T'][-1]
 assert np.isfinite(a).all();maps.append((c,a))
lo=min(float(a.min()) for _,a in maps);hi=max(float(a.max()) for _,a in maps)
fig,axes=plt.subplots(3,4,figsize=(13,9),constrained_layout=True,sharex=True,sharey=True)
columns=[(False,1),(True,1),(False,.5),(True,.5)]
for c,a in maps:
 row='ABC'.index(c['layout']);col=columns.index((c['expanded'],c['dx']));ax=axes[row,col]
 im=ax.imshow(a,origin='lower',extent=(8,14,0,5),vmin=lo,vmax=hi,cmap='inferno',interpolation='nearest',aspect='equal')
 if row==0:ax.set_title(('Expanded' if c['expanded'] else 'Compact')+f" · {c['dx']:g} m cells",fontsize=12)
 if col==0:ax.set_ylabel(f"Layout {c['layout']}\nHeight z (m)")
 if row==2:ax.set_xlabel('Along wall y (m)')
 ax.set_xticks([8,10,12,14]);ax.set_yticks([0,1,2,3,4,5]);ax.text(.03,.96,f"{a.min():.1f}–{a.max():.1f} °C",transform=ax.transAxes,va='top',color='white',fontsize=10,bbox=dict(facecolor='black',alpha=.55,pad=2,edgecolor='none'))
fig.colorbar(im,ax=axes,shrink=.8,label='Wall surface temperature (°C) — shared scale')
fig.suptitle('West wall at 180 seconds · x = 11 m\nNative cell temperatures; no smoothing',fontsize=15)
out=ROOT/'data/analysis';out.mkdir(exist_ok=True);fig.savefig(out/'final-west-wall-all-12.png',dpi=180);fig.savefig(out/'final-west-wall-all-12.pdf');plt.close(fig)
(ROOT/'results/final-wall-maps.json').write_text(json.dumps(dict(time_s=180,face='west x=11m, y8:14m, z0:5m',units='C',shared_scale=[lo,hi],source='Instantaneous WALL TEMPERATURE DEVC at native face cell centres; identical-area pixels, nearest-neighbor rendering',cases=[dict(case=c['case'],min_C=float(a.min()),max_C=float(a.max()),mean_C=float(a.mean())) for c,a in maps]),indent=2));print('Shared range',lo,hi)
