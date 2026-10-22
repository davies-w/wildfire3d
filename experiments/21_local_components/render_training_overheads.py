"""Overhead diagrams of every completed Stage B configuration, from executed decks."""
import json,re,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle,Patch
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/training_overheads';OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'component-development.json').read_text())['cases']
selected=json.loads((ROOT/'results/component-model-selection.json').read_text())['training_cases']
additive=json.loads((ROOT/'data/component_frozen/baseline.json').read_text())['training_cases'] if (ROOT/'data/component_frozen/baseline.json').exists() else json.loads((ROOT/'data/additive_baseline.json').read_text())['training_cases']
completed=[c for c in manifest if (ROOT/'results'/f"{c['case']}-audit.json").exists()]
train=sorted([c for c in completed if c['split']=='train'],key=lambda c:(c['case'] not in selected,selected.index(c['case']) if c['case'] in selected else c['case']))
proof=[]
def nums(s,k):return list(map(float,re.search(r'\b'+k+r'=([-+.\d,]+)',s)[1].rstrip(',').split(',')))
def panel(ax,c):
 name=c['case'];deck=ROOT/'data/cloud'/name/(name+'.fds');deck=deck if deck.exists() else ROOT/'decks'/f'{name}.fds'
 text=deck.read_text();h=hashlib.sha256(deck.read_bytes()).hexdigest();result=json.loads((ROOT/'data/cloud'/name/'result.json').read_text());assert h==result['deck_sha256']
 blocks=lambda typ:re.findall(r'&'+typ+r'\b.*?/',text,re.S)
 mesh=nums(blocks('MESH')[0],'XB');ob=[nums(b,'XB') for b in blocks('OBST')]
 crowns=[dict(xyz=nums(b,'XYZ'),radius=nums(b,'RADIUS')[0],height=nums(b,'HEIGHT')[0]) for b in blocks('INIT') if "PART_ID='foliage'" in b]
 sources=[dict(xyz=nums(b,'XYZ'),radius=nums(b,'RADIUS')[0]) for b in blocks('INIT') if "PART_ID='contact ignitor'" in b]
 for b in sorted(ob,key=lambda b:-b[4]):
  roof=b[4]>=6;ax.add_patch(Rectangle((b[0],b[2]),b[1]-b[0],b[3]-b[2],facecolor='#e4d5bc' if roof else '#66594d',edgecolor='#66594d',alpha=.55 if roof else 1,hatch='//' if roof else None,lw=.7))
 for i,q in enumerate(crowns):
  x,y,z=q['xyz'];ax.add_patch(Circle((x,y),q['radius'],fc='#afd0b8',ec='#2c6847',lw=1.3));ax.text(x,y,f"{z+q['height']:g}m",ha='center',va='center',fontsize=9,color='#163d29')
 for q in sources:
  x,y,z=q['xyz'];ax.add_patch(Circle((x,y),q['radius'],fill=False,ec='#d86213',lw=2,ls='--'))
 ax.add_patch(Rectangle((mesh[0],mesh[2]),mesh[1]-mesh[0],mesh[3]-mesh[2],fill=False,ec='#777',ls=':',lw=1))
 ax.annotate('',xy=(9,3),xytext=(3,3),arrowprops=dict(arrowstyle='->',color='#2267a1',lw=1.8));ax.text(10,3,f"{c['wind_m_s']} m/s",va='center',fontsize=9,color='#2267a1')
 a=json.loads((ROOT/'results'/f'{name}-audit.json').read_text());burn=a['facade_device_burn_max']>1e-9
 label=('GRAPH + ADDITIVE' if name in selected and name in additive else 'GRAPH' if name in selected else 'ADDITIVE / other candidates' if name in additive else 'Other candidates') if c['split']=='train' else c['split'].upper()
 ax.set_title(name.removeprefix('b21_')+'\n'+label,fontsize=11,loc='left',fontweight='bold',pad=8)
 ax.text(.01,-.18,f"Moisture {c['moisture']:.0%}  |  facade {'IGNITED' if burn else 'not ignited'}\nMax facade device: {a['facade_temperature_max_C']:.0f}°C",transform=ax.transAxes,fontsize=9)
 ax.set(xlim=(-1,33),ylim=(-1,25),xticks=[0,8,16,24,32],yticks=[0,8,16,24],xlabel='',ylabel='y (m)');ax.set_aspect('equal');ax.grid(alpha=.12);ax.tick_params(labelsize=8)
 proof.append(dict(case=name,deck_sha256=h,selected_graph=name in selected,additive=name in additive,split=c['split'],canopies=crowns,sources=sources,obstacles=ob))
def sheet(cases,name,title):
 fig,axes=plt.subplots(2,3,figsize=(14.5,10.2));fig.subplots_adjust(top=.85,bottom=.15,hspace=.65,wspace=.27)
 for ax,c in zip(axes.flat,cases):panel(ax,c)
 for ax in list(axes.flat)[len(cases):]:ax.axis('off')
 fig.suptitle(title,fontsize=17,y=.98,fontweight='bold')
 fig.text(.05,.935,'Executed geometry • x/y coordinates in metres • labels inside crowns are TOP height, not diameter',fontsize=11)
 handles=[Patch(fc='#afd0b8',ec='#2c6847',label='Particle canopy envelope'),Line2D([],[],color='#d86213',ls='--',lw=2,label='20 s artificial source ring'),Patch(fc='#66594d',label='Wood wall'),Patch(fc='#e4d5bc',hatch='//',label='Roof / overhang projection')]
 fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.915),ncol=4,frameon=False,fontsize=10)
 fig.text(.05,.055,'All: 90 s, 0.5 m cells; generic vegetation + 20 mm wood thermal layer. Facade: 8 m wide × 6 m high.\nCanopies: 4 m diameter / 10 m top, or 6 m diameter / 16 m top. No trunks, grass, shrubs, fences, interiors or embers.\nColours show geometry, NOT heat or observed burning. Training cases share simplified material assumptions.',fontsize=10,linespacing=1.6)
 fig.savefig(OUT/(name+'.png'),dpi=150,facecolor='white');plt.close(fig)
assert len(train)==12
sheet(train[:6],'training-1','Training configurations 1–6 of 12')
sheet(train[6:],'training-2','Training configurations 7–12 of 12')
sheet([c for c in completed if c['split']!='train'],'validation-controls','Separate validation configurations and source-removal control')
(OUT/'provenance.json').write_text(json.dumps(dict(cases=proof,selected_graph=selected,additive=additive,not_executed=[c['case'] for c in manifest if c not in completed]),indent=2))
print('Wrote 12 training views, 4 validation views, 1 control; verified executed deck hashes.')
