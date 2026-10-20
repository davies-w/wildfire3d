import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
R=Path(__file__).parent;name='s28_test_2';b=np.load(R/f'data/predictions/physical_{name}.npy',mmap_mode='r');i=np.unravel_index(b[:,0].argmin(),b[:,0].shape);t=2*i[0];a=np.load(R/f'data/test-fields/{name}.npy',mmap_mode='r');ts=np.load(R/f'data/test-fields/{name}-time.npy');j=abs(ts-t).argmin();fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,img,label in zip(axes,[a[j,0,:,i[2],:].T,b[i[0],0,:,i[2],:].T],['FDS','Repaired CNN']):
 im=ax.imshow(img,origin='lower',extent=[0,24,0,16],vmin=-70,vmax=70,cmap='coolwarm');ax.set_title(label);ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');ax.scatter([.25+.5*i[1]],[.25+.5*i[3]],facecolors='none',edgecolors='black',s=80)
fig.colorbar(im,ax=axes,label='Temperature (°C); values above70 saturate',extend='max');fig.suptitle(f'Cold artifact diagnostic: {name}, t={t}s, Y={.25+.5*i[2]:.2f}m\nCircle marks CNN minimum; these are physical-temperature predictions, not fire colours.');fig.savefig(R/'results/visuals/cold-artifact.png',dpi=130)
