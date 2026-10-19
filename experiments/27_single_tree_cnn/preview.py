"""Static setup preview; geometry and parameters, not predicted fire."""
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from pathlib import Path
R=Path(__file__).parent;cs=json.loads((R/'cases.json').read_text());fig,ax=plt.subplots(1,3,figsize=(14,4.5))
a=ax[0];a.add_patch(Rectangle((0,0),24,16,fill=False,color='gray'));a.add_patch(Circle((8,8),1.5,color='forestgreen',alpha=.4));theta=np.deg2rad(np.linspace(150,210,100));a.plot(8+1.2*np.cos(theta),8+1.2*np.sin(theta),color='orangered',lw=4);a.arrow(1,8,3,0,width=.08,color='steelblue');a.set(xlim=(-1,25),ylim=(-1,17),aspect='equal',xlabel='X (m)',ylabel='Y (m)',title='Top view: example upwind ignition');a.text(8,12,'Frozen canopy\n3 m base diameter',ha='center');a.text(8,4,'60° source arc; angle varies',ha='center')
a=ax[1];a.plot([6.5,8,9.5,6.5],[2,10,2,2],color='forestgreen');a.axhline(0,color='brown');a.set(xlim=(0,24),ylim=(0,16),aspect='equal',xlabel='X (m)',ylabel='Z (m)',title='Side view: 8 m crown, base at 2 m');a.text(12,7,'No trunk\nBare nonflammable ground\n0.5 m cells',fontsize=9)
a=ax[2]
for label,color,marker,rows in [('train1–8','#2166ac','o',[c for c in cs if c['split']=='train' and c['training_rank']<8]),('train9–16','#67a9cf','o',[c for c in cs if c['split']=='train' and 8<=c['training_rank']<16]),('train17–32','#b4d8e7','o',[c for c in cs if c['split']=='train' and c['training_rank']>=16]),('validation','orange','s',[c for c in cs if c['split']=='validation']),('test','black','x',[c for c in cs if c['split']=='test'])]:
 a.scatter([c['wind_speed'] for c in rows],[c['angle_deg'] for c in rows],label=label,color=color,marker=marker,s=28)
a.set(xlabel='Wind speed (m/s)',ylabel='Ignition angle (°)',xlim=(.8,5.2),ylim=(-10,370),title='Whole simulations define the split');a.legend(fontsize=8)
fig.suptitle('One fixed generic canopy; moisture12%; artificial source20s; no embers');fig.tight_layout();(R/'results/visuals').mkdir(exist_ok=True);fig.savefig(R/'results/visuals/setup.png',dpi=140)
