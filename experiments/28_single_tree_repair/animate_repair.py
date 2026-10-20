"""Common-scale physical-field comparisons, with unthresholded total-HRR traces."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from PIL import Image
import io
R=Path(__file__).parent;out=R/'results/visuals';out.mkdir(exist_ok=True)
for c in [c for c in json.loads((R/'cases.json').read_text()) if c['split']=='test'][:2]:
 name=c['case'];a=np.load(R/f'data/test-fields/{name}.npy',mmap_mode='r');t=np.load(R/f'data/test-fields/{name}-time.npy');tt=np.arange(0,181,2);ix=abs(t[:,None]-tt).argmin(0)
 fields=[a[ix],np.load(R/f'data/predictions/original_{name}.npy',mmap_mode='r'),np.load(R/f'data/predictions/physical_{name}.npy',mmap_mode='r')];labels=['FDS reference','Original CNN','Repaired CNN'];frames=[]
 histories=[np.asarray(x[:,1]).sum((1,2,3))*.125 for x in fields]
 for k in range(0,91,3):
  fig,axes=plt.subplots(3,3,figsize=(11,8),layout='constrained')
  for i,(x,label) in enumerate(zip(fields,labels)):
   im=axes[i,0].imshow(x[k,0].max(axis=1).T,origin='lower',extent=[0,24,0,16],vmin=20,vmax=1400,cmap='inferno');axes[i,0].set_title(label+' temperature (°C)');fig.colorbar(im,ax=axes[i,0],shrink=.7,extend='max')
   im=axes[i,1].imshow(np.maximum(x[k,1].max(axis=1).T,.01),origin='lower',extent=[0,24,0,16],norm=LogNorm(.01,1000),cmap='magma');axes[i,1].set_title('Heat release (kW/m³)');fig.colorbar(im,ax=axes[i,1],shrink=.7,extend='both')
   for j,h in enumerate(histories):axes[i,2].plot(tt,h,label=labels[j],alpha=1 if j==i else .25)
   axes[i,2].axvline(tt[k],color='black');axes[i,2].set_yscale('symlog',linthresh=.1);axes[i,2].set_ylim(0,max(h.max() for h in histories)*1.2);axes[i,2].set_title(f'Total heat: {histories[i][k]:.3g} kW');axes[i,2].set_xlabel('Seconds');axes[i,2].legend(fontsize=7)
  fig.suptitle(f'{name}: {tt[k]} s | wind {c["wind_speed"]:.2f} m/s, ignition {c["angle_deg"]:.1f}°\nY-max projection; colours cap at1400°C/1000kW/m³. Heat below0.01 is colour-floor only. No embers.',fontsize=11)
  buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=85);plt.close(fig);buffer.seek(0);frames.append(Image.open(buffer).convert('RGB').copy())
 frames[0].save(out/f'{name}.gif',save_all=True,append_images=frames[1:],duration=180,loop=0);print(name,flush=True)
