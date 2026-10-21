"""Render preselected held-out projections with shared scales, not volumetric flame rendering."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from PIL import Image
R=Path(__file__).parent

def main():
 report=json.loads((R/'results/fresh-test-evaluation.json').read_text());cs={c['case']:c for c in json.loads((R/'fresh-tests.json').read_text())};names=report['projections'];fig,axs=plt.subplots(len(names),2,figsize=(12,3*len(names)),constrained_layout=True)
 for i,n in enumerate(names):
  c=cs[n];rows=[h for h in report['histories'] if h['case']==n]
  for j,(truth,pred,label) in enumerate([('truth_heat_kW','predicted_heat_kW','Total gas heat release (kW)'),('truth_peak_C','predicted_peak_C','Peak gas temperature (C)')]):
   ax=axs[i,j];ax.plot(rows[0]['time_s'],rows[0][truth],color='black',label='FDS')
   for h in rows:ax.plot(h['time_s'],h[pred],label=h['model'])
   ax.axvline(20,color='gray',ls=':');ax.set(xlabel='Physical time (s)',ylabel=label,title=f"{n}: {c['crown_height_m']}m crown, moisture{c['moisture']}, wind{c['wind_speed']}m/s");ax.legend(fontsize=7);ax.grid(alpha=.2)
 fig.savefig(R/'results/fresh-histories.png',dpi=130);plt.close(fig)
 for n in names:
  c=cs[n];z=np.load(R/'data/evaluation'/('projection-'+n+'.npz'));times=z['time'];frames=[]
  for k in range(0,len(times),3):
   fig,axes=plt.subplots(2,3,figsize=(10,5),constrained_layout=True)
   for col,(key,label) in enumerate([('fds','FDS reference'),('snapshot','Snapshot CNN'),('hybrid','Snapshot + recurrent correction')]):
    for row in [0,1]:
     im=axes[row,col].imshow(z[key][k,row].T,origin='lower',extent=[0,24,0,16],cmap='inferno',norm=PowerNorm(.45,vmin=20 if row==0 else 0,vmax=1600 if row==0 else 3000),aspect='equal');axes[row,col].set(xlabel='x (m)',ylabel='z (m)');axes[row,col].set_title(label if row==0 else '',fontsize=9);axes[row,col].plot([6.5,8,9.5,6.5],[2,2+c['crown_height_m'],2,2],color='cyan',ls='--',lw=.7)
   for row,label in [(0,'Gas temperature (C)'),(1,'Heat release density (kW/m3)')]:fig.colorbar(axes[row,0].images[0],ax=axes[row,:],shrink=.6,label=label)
   fig.suptitle(f"{n} | t={times[k]:.0f}s | height{c['crown_height_m']}m, moisture{c['moisture']}, wind{c['wind_speed']}m/s\nMax through y, not a slice/flame render. Cyan: crown envelope. Source0-20s; no embers. Shared scales clip peaks.",fontsize=9)
   fig.canvas.draw();frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert('RGB'));plt.close(fig)
  frames[0].save(R/'results'/(n+'-comparison.gif'),save_all=True,append_images=frames[1:],duration=200,loop=0)
 print('Rendered',len(names),'preselected held-out comparisons')
if __name__=='__main__':main()
