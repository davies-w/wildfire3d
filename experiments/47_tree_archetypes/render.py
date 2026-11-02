"""Dimensioned abstract vegetation concepts; geometry only, no solver or training."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'data';D.mkdir(exist_ok=True)
# Ellipsoids: centre and semi-axes. Cones: centre x/y, base, top, radius.
trees=[
 dict(name='Tall conifer',hint='Pine / Douglas-fir-like',color='#247b69',cones=[[0,0,6,14,3.5],[0,0,10,18,2.8],[0,0,14,20,1.8]],ellipsoids=[],stems=[[[0,0,0],[0,0,19],.22]]),
 dict(name='Broad oak',hint='Low, spreading crown',color='#6b8f36',cones=[],ellipsoids=[[0,0,6.5,4.4,4.2,3.5],[-3,0,5.5,3,3.2,2.5],[3,.4,6,3,3,2.7]],stems=[[[0,0,0],[0,0,4],.35],[[0,0,3],[-3,0,6],.20],[[0,0,3],[3,.4,6.5],.20]]),
 dict(name='Tall open crown',hint='Eucalyptus-like; separated clumps',color='#58a69c',cones=[],ellipsoids=[[-3,0,15,2.5,2.2,3],[3,.7,17,2.5,2.2,3],[.2,-.7,21,2.7,2.3,3]],stems=[[[0,0,0],[.2,-.7,22],.28],[[0,0,10],[-3,0,15],.16],[[0,0,12],[3,.7,17],.16]]),
 dict(name='Dense narrow evergreen',hint='Cypress / screening-tree-like',color='#326642',cones=[],ellipsoids=[[0,0,6.4,1.5,1.5,5.6]],stems=[[[0,0,0],[0,0,11],.16]]),
 dict(name='Low multi-stem',hint='Toyon / large-manzanita-like',color='#929744',cones=[],ellipsoids=[[-1.2,0,2.8,1.8,2,2],[1.2,.4,3,1.8,1.8,2],[0,-1.1,2.4,1.7,1.5,1.6]],stems=[[[0,0,0],[-1.2,0,3],.12],[[.2,.1,0],[1.2,.4,3.4],.12],[[-.2,0,0],[0,-1.1,2.8],.10]])]
u=np.linspace(0,2*np.pi,45);v=np.linspace(0,np.pi,27)
def bounds(t):
 boxes=[]
 for x,y,z,rx,ry,rz in t['ellipsoids']:boxes.append([x-rx,x+rx,y-ry,y+ry,z-rz,z+rz])
 for x,y,b,h,r in t['cones']:boxes.append([x-r,x+r,y-r,y+r,b,h])
 b=np.array(boxes);return [float(b[:,0].min()),float(b[:,1].max()),float(b[:,2].min()),float(b[:,3].max()),float(b[:,4].min()),float(b[:,5].max())]
def stem(ax,start,end,r):
 start=np.array(start);end=np.array(end);axis=(end-start)/np.linalg.norm(end-start);ref=np.array([1.,0,0]);e=np.cross(axis,ref);e/=np.linalg.norm(e);f=np.cross(axis,e)
 ring=r*(np.cos(u)[:,None]*e+np.sin(u)[:,None]*f);xyz=np.stack([start+ring,end+ring]);ax.plot_surface(xyz[:,:,0],xyz[:,:,1],xyz[:,:,2],color='#795c45',shade=True,alpha=1)
def draw(ax,t,shared=False):
 for start,end,r in t['stems']:stem(ax,start,end,r)
 for x,y,z,rx,ry,rz in t['ellipsoids']:
  X=x+rx*np.outer(np.cos(u),np.sin(v));Y=y+ry*np.outer(np.sin(u),np.sin(v));Z=z+rz*np.outer(np.ones_like(u),np.cos(v));ax.plot_surface(X,Y,Z,color=t['color'],alpha=.38,linewidth=0,shade=True)
 for x,y,b,h,r in t['cones']:
  q=np.linspace(0,1,25);X=x+r*np.outer(np.cos(u),1-q);Y=y+r*np.outer(np.sin(u),1-q);Z=b+(h-b)*np.outer(np.ones_like(u),q);ax.plot_surface(X,Y,Z,color=t['color'],alpha=.4,linewidth=0,shade=True)
 b=bounds(t);span=max(b[1]-b[0],b[3]-b[2])+2;top=b[5];span=14 if shared else span;lim=26 if shared else top+1
 ax.set(xlim=(-span/2,span/2),ylim=(-span/2,span/2),zlim=(0,lim));ax.set_box_aspect((span,span,lim));ax.view_init(19,-58);ax.set_xticks([]);ax.set_yticks([]);ax.set_zticks([0,round(top/2,1),top]);ax.tick_params(axis='z',labelsize=8,pad=0);ax.set_zlabel('metres',fontsize=8,labelpad=1)
 for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.pane.fill=False;axis.pane.set_edgecolor('#e5e9eb')
 ax.grid(False);ax.plot([-span/2,span/2],[0,0],[0,0],color='#c5cdd0',lw=1);ax.plot([0,0],[-span/2,span/2],[0,0],color='#c5cdd0',lw=1)
 ax.set_title(t['name'],fontsize=12,fontweight='bold',pad=14)
 ax.text2D(.5,-.13,f"{top:g} m tall · {b[1]-b[0]:g} m wide\nCrown begins {b[4]:g} m above ground",transform=ax.transAxes,ha='center',fontsize=9,color='#394b55')
for shared in [False,True]:
 fig=plt.figure(figsize=(18,7),facecolor='white');fig.suptitle('Five abstract California-interface tree forms'+(' — same scale' if shared else ''),fontsize=21,fontweight='bold',y=.95)
 for i,t in enumerate(trees):draw(fig.add_subplot(1,5,i+1,projection='3d'),t,shared)
 fig.subplots_adjust(left=.015,right=.985,bottom=.19,top=.83,wspace=.06)
 fig.text(.5,.065,('All panels use the same metre scale.' if shared else 'Each panel is zoomed to its tree; proportions within each panel are true.')+'  Translucent green = proposed crown envelope; brown = simplified stems.',ha='center',fontsize=11)
 fig.text(.5,.028,'Geometry concepts only: colours do not encode fuel density. Overlapping crown pieces form a union, not extra fuel. No fire, moisture, bark shedding or embers simulated.',ha='center',fontsize=10,color='#52616b')
 fig.savefig(D/('five-trees-same-scale.png' if shared else 'five-trees.png'),dpi=170);plt.close(fig)
for i,t in enumerate(trees):
 fig=plt.figure(figsize=(7,8));draw(fig.add_subplot(111,projection='3d'),t);fig.subplots_adjust(bottom=.15);fig.savefig(D/f'tree-{i+1}.png',dpi=150);plt.close(fig)
for t in trees:t['crown_bounds_m']=bounds(t)
(D/'geometry.json').write_text(json.dumps({'units':'m','scope':'Proposed abstract geometry, not species-calibrated fuel or combustion models','overlap_rule':'Union of crown primitives; no double-counting fuel in overlaps','trees':trees},indent=2)+'\n')
