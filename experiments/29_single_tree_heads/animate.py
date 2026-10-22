"""Development-validation animation; physical time and common colour scales."""
import io,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from PIL import Image
from original_cnn import ROOT,load
c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='validation');a,t=load(c);arrays=[a]+[np.load(ROOT/f"data/validation_predictions/{n}_{c['case']}.npy",mmap_mode='r') for n in ['previous','bounded','heads']];labels=['FDS','Previous CNN','Bounded-temperature CNN','Separate heads + fire strength'];frames=[]
for k in range(0,len(t),3):
 fig,axes=plt.subplots(4,2,figsize=(10,10),layout='constrained')
 for row,(x,label) in enumerate(zip(arrays,labels)):
  im=axes[row,0].imshow(x[k,0].max(1).T,origin='lower',extent=[0,24,0,16],vmin=6,vmax=1600,cmap='inferno');axes[row,0].set_title(label+' — gas temperature (°C)',fontsize=10);fig.colorbar(im,ax=axes[row,0],shrink=.7,extend='both')
  im=axes[row,1].imshow(np.maximum(x[k,1].max(1).T,.01),origin='lower',extent=[0,24,0,16],norm=LogNorm(.01,1000),cmap='magma');axes[row,1].set_title(f'Heat release: total {x[k,1].sum()*.125:.2f} kW',fontsize=10);fig.colorbar(im,ax=axes[row,1],shrink=.7,extend='both')
 fig.suptitle(f'DEVELOPMENT VALIDATION (used for model selection): {t[k]:.1f}s\nY-max projections; HRR colour floor0.01kW/m³, cap1000; temperature6–1600°C.\nPrevious model cold undershoot hidden by projection/colour floor; numerical report includes it.',fontsize=10)
 b=io.BytesIO();fig.savefig(b,format='png',dpi=90);plt.close(fig);b.seek(0);frames.append(Image.open(b).convert('RGB').copy())
frames[0].save(ROOT/'results/visuals/validation-comparison.gif',save_all=True,append_images=frames[1:],duration=180,loop=0);frames[4].save(ROOT/'results/visuals/validation-preview.png');print('Animation saved',flush=True)
