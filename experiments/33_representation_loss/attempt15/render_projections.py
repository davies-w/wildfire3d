"""Render preselected maximum-through-y gas fields; never literal flame geometry."""
from pathlib import Path
import json,io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from PIL import Image
R=Path(__file__).parent
z=np.load(R/'data/collected/projections.npz');plan=json.loads((R/'coverage-plan.json').read_text());cs={c['case']:c for c in json.loads((R/'cases.json').read_text())};out=R/'data/visuals';out.mkdir(parents=True,exist_ok=True)
arms=['FDS','initial','control','strength_low','strength_high'];labels=['FDS reference','Saved expanded360','Unchanged loss','Strength weight 0.02','Strength weight 0.1']
tmax=max(float(z[n+'_'+a][:,0].max()) for n in plan['animation_cases'] for a in arms);qmax=max(float(z[n+'_'+a][:,1].max()) for n in plan['animation_cases'] for a in arms);tmax=max(100,np.ceil(tmax/100)*100);qmax=max(10,np.ceil(qmax/100)*100)
records=[]
for n in plan['animation_cases']:
 c=cs[n];times=z[n+'_time'];fig,axs=plt.subplots(2,5,figsize=(14,5.6),layout='constrained');images=[]
 for row in range(2):
  cmap=plt.get_cmap('inferno').copy();cmap.set_under('#368fa5' if row==0 else '#000000')
  norm=PowerNorm(.45 if row==0 else .3,vmin=20 if row==0 else 0,vmax=tmax if row==0 else qmax,clip=False)
  for j,a in enumerate(arms):
   ax=axs[row,j];im=ax.imshow(z[n+'_'+a][0,row].T,origin='lower',extent=(0,24,0,16),aspect='equal',cmap=cmap,norm=norm);images.append(im);ax.set_xlabel('x (m)');ax.set_ylabel('z (m)' if j==0 else '');ax.set_title(labels[j] if row==0 else '');ax.set_xticks([0,12,24]);ax.set_yticks([0,8,16])
  fig.colorbar(images[-1],ax=list(axs[row,:]),shrink=.8,label='Gas temperature (°C)' if row==0 else 'Heat release density (kW/m³)',extend='min' if row==0 else 'neither')
 title=fig.suptitle('');frames=[];peak=int(np.argmax(z[n+'_FDS'][:,1].sum((1,2))));ids=sorted(set(list(range(0,len(times),2))+[len(times)-1,peak]))
 for k in ids:
  for row in range(2):
   for j,a in enumerate(arms):images[row*5+j].set_data(z[n+'_'+a][k,row].T)
  title.set_text(f'{n}: {c["crown_height_m"]:g} m crown above 2 m base; wind {c["wind_speed"]:g} m/s; moisture {100*c["moisture"]:g}% dry basis | t={times[k]:.0f} s\nMax through y; shared nonlinear scales across all cases/models. Cyan: gas below 20°C. Not flame geometry.')
  buf=io.BytesIO();fig.savefig(buf,format='png',dpi=90);buf.seek(0);image=Image.open(buf).convert('RGB');frames.append(image.copy())
  if k==peak:image.save(out/(n+'-preview.png'))
 frames[0].save(out/(n+'.gif'),save_all=True,append_images=frames[1:],duration=180,loop=0,optimize=False);plt.close(fig)
 records.append(dict(case=n,preview_time_s=float(times[peak]),gif=n+'.gif',preview=n+'-preview.png',frames=len(frames)))
(out/'manifest.json').write_text(json.dumps(dict(scope='Preselected existing development cases, maximum-through-y gas temperature and heat release. No physical validation. Nonlinear display mapping only; recorded seconds on frames. Frame playback is accelerated, not real time.',temperature_max_C=tmax,heat_release_max_kW_m3=qmax,cases=records),indent=2))
print(json.dumps(records))
