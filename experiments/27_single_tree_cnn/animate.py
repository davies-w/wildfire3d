"""Matched scientific GIFs: same projections, units and scales for reference/CNN."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm,LogNorm
from matplotlib.animation import FuncAnimation,PillowWriter
from cnn import ROOT,load

def main():
 out=ROOT/'results/visuals';out.mkdir(exist_ok=True)
 for c in [c for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='test'][:2]:
  a,t=load(c);times=np.arange(0,181,4);ix=abs(t[:,None]-times).argmin(0);a=np.array(a[ix]);b=np.load(ROOT/'data/predictions'/f"cnn_32_{c['case']}.npy")[::2]
  # Max along Y gives an X-Z envelope; fields remain full3D in saved evidence.
  fields=[[a[:,0].max(2),a[:,1].max(2),a[:,5].max(2)],[b[:,0].max(2),b[:,1].max(2),b[:,5].max(2)]]
  fig,axes=plt.subplots(2,3,figsize=(12,7));images=[]
  norms=[PowerNorm(.45,vmin=20,vmax=max(100,float(max(a[:,0].max(),b[:,0].max())))),LogNorm(vmin=.1,vmax=max(10,float(max(a[:,1].max(),b[:,1].max()))),clip=True),PowerNorm(.5,vmin=0,vmax=max(2,float(max(a[:,5].max(),b[:,5].max()))))]
  for r in range(2):
   for k in range(3):
    ax=axes[r,k];im=ax.imshow(fields[r][k][0].T,origin='lower',extent=[0,24,0,16],norm=norms[k],cmap=['inferno','magma','inferno'][k],aspect='equal');images.append(im)
    ax.plot([6.5,8,9.5,6.5],[2,10,2,2],color='cyan',lw=.6,alpha=.6);ax.set_title(('FDS' if r==0 else 'CNN · 32 training cases')+'\n'+['Gas temperature','Combustion intensity','Radiation intensity'][k],fontsize=10);ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');fig.colorbar(im,ax=ax,shrink=.7,label=['°C','kW/m³','kW/m²'][k])
  title=fig.suptitle('');fig.text(.5,.02,'Maximum along Y; cyan = canopy outline. HRRPUV ≤0.1 kW/m³ uses the darkest colour; not a visible-flame rendering.\nGeneric 8 m canopy at z=2 m; 0.5 m grid; fixed moisture; artificial source0–20s; no embers.',ha='center',fontsize=9)
  fig.tight_layout(rect=[0,.08,1,.93])
  def update(i):
   for r in range(2):
    for k in range(3):images[r*3+k].set_data(fields[r][k][i].T)
   title.set_text(f"{c['case']} | wind {c['wind_speed']:.2f} m/s | ignition {c['angle_deg']:.0f}° | {times[i]:.0f} s")
   return images+[title]
  animation=FuncAnimation(fig,update,frames=len(times),interval=160);animation.save(out/(c['case']+'.gif'),writer=PillowWriter(fps=6),dpi=100);plt.close(fig)
if __name__=='__main__':
 main()
 from animate_3d import main as render3d
 render3d()
