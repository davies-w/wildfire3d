"""Fixed-scale projected temperature/combustion views and full-volume heat histories."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from PIL import Image
from alignment import align_reference
R=Path(__file__).parent

def main():
 report=json.loads((R/'results/fresh-test-evaluation.json').read_text());cs=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='test'];fig,axs=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
 for i,c in enumerate(cs):
  rows=[h for h in report['histories'] if h['case']==c['case']]
  for j,(truth,pred,label) in enumerate([('truth_heat_kW','predicted_heat_kW','Total gas heat release (kW)'),('truth_peak_C','predicted_peak_C','Peak gas temperature (°C)')]):
   ax=axs[i,j];ax.plot(rows[0]['time_s'],rows[0][truth],color='black',label='FDS')
   for h in rows:ax.plot(h['time_s'],h[pred],label=h['model'])
   ax.axvline(20,color='gray',ls=':',label='Source off' if j==0 else None);ax.set(xlabel='Physical time (s)',ylabel=label,title=f"{c['case']}: crown {c['crown_height_m']} m, loading {c['loading_multiplier']}");ax.legend(fontsize=7);ax.grid(alpha=.2)
 fig.savefig(R/'results/fresh-histories.png',dpi=150);plt.close(fig)
 for c in cs:
  name=c['case'];truth=np.load(R/'data/fields'/(name+'.npy'),mmap_mode='r');times=np.load(R/'data/fields'/(name+'-time.npy'));wanted=np.load(R/'data/predictions'/('snapshot_'+name+'.npz'))['time'];truth,_=align_reference(truth,times,wanted);times=wanted;datasets=[truth]+[np.load(R/'data/predictions'/(m+'_'+name+'.npz'))['fields'] for m in ['snapshot','hybrid','state_reset_ablation']];names=['FDS reference','Geometry snapshot CNN','Snapshot + recurrent correction','Correction with state reset'];frames=[]
  for k in range(0,len(times),3):
   fig,axes=plt.subplots(2,4,figsize=(12,4.5),constrained_layout=True)
   for col,(a,label) in enumerate(zip(datasets,names)):
    for row,ch in enumerate([0,1]):
     # Maximum along y; a projection, not a slice or physical flame rendering.
     z=a[k,ch].max(axis=1).T;norm=PowerNorm(.45,vmin=20 if ch==0 else 0,vmax=1600 if ch==0 else 3000);im=axes[row,col].imshow(z,origin='lower',extent=[0,24,0,16],cmap='inferno',norm=norm,aspect='equal');axes[row,col].set(xlabel='x (m)',ylabel='z (m)');axes[row,col].set_title(label if row==0 else '',fontsize=9);axes[row,col].plot([6.5,8,9.5,6.5],[2,2+c['crown_height_m'],2,2],color='cyan',ls='--',lw=.6,alpha=.6)
   fig.colorbar(axes[1,0].images[0],ax=axes[1,:],shrink=.8,label='kW/m³')
   # Separate temperature scale, common to all models.
   fig.colorbar(axes[0,0].images[0],ax=axes[0,:],shrink=.6,label='°C');fig.suptitle(f'{name} — t={times[k]:.0f}s — maximum through y: gas temperature / heat-release density\nDashed cyan: crown envelope. Artificial source 0–20s; no embers. Fixed scales clip peaks. Not a flame rendering.',fontsize=10)
   fig.canvas.draw();im=Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert('RGB');frames.append(im);plt.close(fig)
  frames[0].save(R/'results'/f'{name}-comparison.gif',save_all=True,append_images=frames[1:],duration=200,loop=0)
 print('Saved two held-out comparison animations and heat histories')
if __name__=='__main__':main()
