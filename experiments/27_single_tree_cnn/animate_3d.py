"""3D voxel-boundary envelopes at native0.5m spacing; not Smokeview flame appearance."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from cnn import ROOT,load

def faces(mask):
 out=[]
 for axis in range(3):
  other=[j for j in range(3) if j!=axis]
  for side in [0,1]:
   neighbor=np.roll(mask,1 if side==0 else -1,axis=axis);sl=[slice(None)]*3;sl[axis]=0 if side==0 else -1;neighbor[tuple(sl)]=False
   idx=np.argwhere(mask&~neighbor);offset=np.zeros((4,3));offset[:,axis]=side;offset[:,other[0]]=[0,1,1,0];offset[:,other[1]]=[0,0,1,1]
   if len(idx):out.append((idx[:,None,:]+offset[None,:,:])*.5)
 return np.concatenate(out) if out else np.empty((0,4,3))
def render(c,a,b,t,path,preview=False):
 fig=plt.figure(figsize=(12,5.5));axes=[fig.add_subplot(1,2,i+1,projection='3d') for i in range(2)];collections=[]
 for ax,label in zip(axes,['FDS reference','CNN prediction (32 training cases)']):
  if preview:label='Renderer check: identical FDS input'
  ax.set(xlim=(0,24),ylim=(0,16),zlim=(0,16),xlabel='X (m)',ylabel='Y (m)',zlabel='Z (m)',title=label);ax.set_box_aspect((24,16,16));ax.view_init(elev=20,azim=-65)
  th=np.linspace(0,2*np.pi,50);ax.plot(8+1.5*np.cos(th),8+1.5*np.sin(th),np.full(50,2),color='forestgreen',lw=1)
  for angle in np.linspace(0,2*np.pi,5)[:-1]:ax.plot([8+1.5*np.cos(angle),8],[8+1.5*np.sin(angle),8],[2,10],color='forestgreen',lw=1)
 title=fig.suptitle('');fig.text(.5,.02,'Red transparent boundary: gas >100°C. Orange boundary: HRRPUV >10 kW/m³. Green: canopy geometry.\nNative0.5m voxel envelopes, not visible-flame rendering. Artificial source0–20s; generic crown; no embers.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.09,1,.92])
 def update(i):
  for poly in collections:poly.remove()
  collections.clear()
  for ax,v in zip(axes,[a,b]):
   for mask,color,alpha in [(v[i,0]>100,'crimson',.12),(v[i,1]>10,'darkorange',.75)]:
    fs=faces(mask)
    if len(fs):
     p=Poly3DCollection(fs,facecolor=color,edgecolor='none',alpha=alpha);ax.add_collection3d(p);collections.append(p)
  title.set_text(f"{c['case']} | {c['wind_speed']:.2f} m/s | ignition {c['angle_deg']:.0f}° | {t[i]:.0f} s")
  return collections+[title]
 animation=FuncAnimation(fig,update,frames=len(t),interval=160);animation.save(path,writer=PillowWriter(fps=6),dpi=100);plt.close(fig)
def main():
 out=ROOT/'results/visuals';out.mkdir(exist_ok=True)
 for c in [c for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='test'][:2]:
  a,t=load(c);times=np.arange(0,181,4);ix=abs(t[:,None]-times).argmin(0);a=np.array(a[ix]);b=np.load(ROOT/'data/predictions'/f"cnn_32_{c['case']}.npy")[::2];render(c,a,b,times,out/(c['case']+'-3d.gif'))
if __name__=='__main__':main()
