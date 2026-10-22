"""Overhead inputs in the same row/column order as the wall heat maps."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
ROOT=Path(__file__).parent
fig,axes=plt.subplots(3,4,figsize=(13,10),constrained_layout=True,sharex=True,sharey=True)
columns=[(False,1),(True,1),(False,.5),(True,.5)]
for row,(layout,receiver) in enumerate(zip('ABC',[(6,12),(5,11),(7,15)])):
 for col,(expanded,dx) in enumerate(columns):
  ax=axes[row,col];lo,hi=(-6,26) if expanded else (0,20)
  ax.add_patch(Rectangle((lo,lo),hi-lo,hi-lo,facecolor='#f4f7fa',edgecolor='#555555',lw=1.3))
  # Draw the actual cell spacing within the simulated horizontal domain.
  import numpy as np
  for q in np.arange(lo+dx,hi,dx):
   ax.plot([q,q],[lo,hi],color='#d5dce3',lw=.3,zorder=1);ax.plot([lo,hi],[q,q],color='#d5dce3',lw=.3,zorder=1)
  ax.add_patch(Rectangle((11,8),6,6,facecolor='#d28b44',edgecolor='#704521',lw=1.2,zorder=3))
  ax.text(14,11,'Wall\nblock',ha='center',va='center',fontsize=8,zorder=5)
  for xy,label in [((5,6),'S'),(receiver,'R')]:
   ax.add_patch(Circle(xy,2,facecolor='#79b7a2',edgecolor='#28604f',lw=1.2,zorder=3));ax.text(*xy,label,ha='center',va='center',fontsize=9,zorder=5)
  ax.add_patch(Circle((5,6),1.5,fill=False,edgecolor='#be3065',lw=1.5,zorder=4))
  ax.plot([11,11],[8,14],color='#b32020',lw=3,zorder=5)
  ax.annotate('',xy=(16,22),xytext=(8,22),arrowprops=dict(arrowstyle='->',color='#333333',lw=1.3));ax.text(12,23,'Wind 3 m/s',ha='center',fontsize=8)
  if row==0:ax.set_title(('Expanded' if expanded else 'Compact')+f' · {dx:g} m cells',fontsize=11)
  if col==0:ax.set_ylabel(f'Layout {layout}\ny (m)')
  if row==2:ax.set_xlabel('x (m)')
  ax.set(xlim=(-7,27),ylim=(-7,27),aspect='equal',xticks=[0,10,20],yticks=[0,10,20])
  ax.text(.03,.03,('32 × 32 × 24 m' if expanded else '20 × 20 × 15 m'),transform=ax.transAxes,fontsize=8)
fig.suptitle('Overhead layouts · same order as the wall heat maps\nS: initialized canopy · R: receiver canopy · red edge: plotted west wall',fontsize=13)
fig.supxlabel('Canopy envelopes: 4 m diameter; source top 10 m, receiver top 8 m. Building: 6 × 6 × 5 m.\nPink ring: artificial source. Colours identify inputs, not temperature. All panels share the same spatial scale.',fontsize=10)
out=ROOT/'data/analysis';fig.savefig(out/'layouts-matched-12.png',dpi=180);fig.savefig(out/'layouts-matched-12.pdf');plt.close(fig)
