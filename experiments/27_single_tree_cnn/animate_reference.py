"""Interim FDS-only preview; no CNN output shown."""
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from animate_3d import faces
from cnn import ROOT,load
c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['case']=='s27_train_0');a,t=load(c);a=np.array(a[::2]);t=t[::2]
fig=plt.figure(figsize=(10,5.5));ax=fig.add_subplot(121,projection='3d');heat=fig.add_subplot(122)
ax.set(xlim=(0,24),ylim=(0,16),zlim=(0,16),xlabel='X (m)',ylabel='Y (m)',zlabel='Z (m)',title='FDS heat/combustion envelopes');ax.set_box_aspect((24,16,16));ax.view_init(elev=20,azim=-65)
for angle in np.linspace(0,2*np.pi,5)[:-1]:ax.plot([8+1.5*np.cos(angle),8],[8+1.5*np.sin(angle),8],[2,10],color='forestgreen',lw=1)
im=heat.imshow(a[0,0].max(1).T,origin='lower',extent=[0,24,0,16],vmin=20,vmax=1600,cmap='inferno');heat.set(xlabel='X (m)',ylabel='Z (m)',title='FDS temperature: maximum along Y');fig.colorbar(im,ax=heat,shrink=.6,label='°C');title=fig.suptitle('');polys=[]
fig.text(.5,.02,'FDS ONLY — no learned prediction. Red: >100°C gas; orange: >10 kW/m³ combustion; green: canopy.\nGeneric 8 m crown above2 m bare ground;0.5 m cells; artificial source0–20s; no embers.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.1,1,.93])
def update(i):
 for p in polys:p.remove()
 polys.clear()
 for mask,color,alpha in [(a[i,0]>100,'crimson',.12),(a[i,1]>10,'darkorange',.75)]:
  f=faces(mask)
  if len(f):p=Poly3DCollection(f,facecolor=color,edgecolor='none',alpha=alpha);ax.add_collection3d(p);polys.append(p)
 im.set_data(a[i,0].max(1).T);title.set_text(f"FDS training case0 | wind {c['wind_speed']:.2f} m/s | ignition {c['angle_deg']:.0f}° | {t[i]:.0f} s")
 return polys+[im,title]
out=ROOT/'results/visuals';out.mkdir(exist_ok=True);FuncAnimation(fig,update,frames=len(t),interval=160).save(out/'fds-reference-preview.gif',writer=PillowWriter(fps=6),dpi=100)
