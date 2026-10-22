"""Show the actual graph component definitions, not separately trained modules."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
import component_hot_state_model as hot
R=Path(__file__).resolve().parent;out=R/'data/individual_components';out.mkdir(exist_ok=True)
r=json.loads((R/'data/component_states/b21_transfer_hot.json').read_text());g=hot.series(r)['g'];crowns=[n for n in g['nodes'] if n['kind']=='vegetation']
f=json.loads((R/'data/component_states/b21_single_1.json').read_text());patches=[n for n in hot.series(f)['g']['nodes'] if n['kind']=='building'];assert len(patches)==48
fig,axs=plt.subplots(2,2,figsize=(13,12));fig.subplots_adjust(left=.08,right=.96,top=.88,bottom=.24,hspace=.85,wspace=.35)
fig.suptitle('Individual components used by the graph model',fontsize=20,fontweight='bold',y=.97)
fig.text(.08,.925,'Canopies are whole-node components. Building surfaces are many separate patch nodes.',fontsize=12)
for ax,c,title,base in zip(axs[0],crowns,['Small canopy: ONE node','Large canopy: ONE node'],[3,5]):
 rad=c['radius'];ax.add_patch(Circle((0,0),rad,fc='#afd0b8',ec='#27623e',lw=2));ax.plot(0,0,'o',color='#153d28',ms=7);ax.annotate('',xy=(rad,-rad-.5),xytext=(-rad,-rad-.5),arrowprops=dict(arrowstyle='<->',color='#263238'));ax.text(0,-rad-.85,f'Diameter {2*rad:g} m',ha='center',fontsize=11)
 ax.set(xlim=(-4,4),ylim=(-4.5,4),xticks=[-4,0,4],yticks=[-4,0,4],xlabel='x relative to canopy centre (m)',ylabel='y relative to canopy centre (m)');ax.set_aspect('equal');ax.set_title(title+' — overhead',fontsize=13,loc='left',pad=10)
 ax.text(.0,-.38,f"Base {base} m; top {base+c['height']:g} m; conical particle envelope.\nFDS foliage + three roundwood classes → one graph state.",transform=ax.transAxes,fontsize=10)
ax=axs[1,0];ax.add_patch(Rectangle((0,0),1,1,fc='#ddc6a6',ec='#695947',lw=2));ax.plot(.5,.5,'o',color='#695947');ax.set(xlim=(-.2,1.2),ylim=(-.2,1.2),xticks=[0,.5,1],yticks=[0,.5,1],xlabel='surface horizontal coordinate (m)',ylabel='surface vertical coordinate (m)');ax.set_aspect('equal');ax.set_title('One building patch: ONE node — face view',fontsize=13,loc='left',pad=10)
ax.text(0,-.38,'Typical training patch: 1 m²; assigned surface orientation.\n20 mm wood thermal layer, advanced by a heat-conduction solver.\nWall / roof / underside use this node type, with different normals.',transform=ax.transAxes,fontsize=10)
ax=axs[1,1]
for p in patches:
 _,y,z=p['xyz'];ax.add_patch(Rectangle((y-8.5,z-.5),1,1,fc='#ddc6a6',ec='#fff',lw=1));ax.plot(y-8,z,'o',color='#695947',ms=2)
ax.set(xlim=(0,8),ylim=(0,6),xticks=[0,2,4,6,8],yticks=[0,2,4,6],xlabel='width (m)',ylabel='height (m)');ax.set_aspect('equal');ax.set_title('Training facade: 48 patch nodes — face view',fontsize=13,loc='left',pad=10)
ax.text(0,-.38,'8 m × 6 m facade = 8 × 6 nodes.\nOne canopy + this facade = 49 graph nodes.\nA building corner was NOT a separately learned component.',transform=ax.transAxes,fontsize=10)
fig.text(.08,.045,'Canopy state: mean / max temperature, wet mass fraction, fuel-release proxy, fractions above 300°C / 500°C.\nShared learned rules connect nodes; there is no separately trained model for each pictured component.\nGeneric materials; no trunks, groundcover or embers. Geometry colours do not indicate heat or burning.',fontsize=11,linespacing=1.5)
fig.savefig(out/'components.png',dpi=150,facecolor='white');plt.close(fig)
(out/'definitions.json').write_text(json.dumps(dict(canopies=crowns,facade_patches=patches,scope='Graph nodes extracted from executed training configurations; no independent component-training simulations implied.'),indent=2))
