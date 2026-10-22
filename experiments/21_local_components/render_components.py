"""Static geometry diagrams parsed from the executed FDS decks, not fire renders."""
import re,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/component_images';OUT.mkdir(exist_ok=True)
NAMES=['a21_single','a21_double','a21_corner','a21_bare','a21_single_expanded','a21_double_expanded','a21_corner_expanded','a21_double_fine']
TITLES=['One canopy + facade','Two canopies + facade','Canopy + corner / overhang','Bare-source control','One canopy + building mass','Two canopies + building mass','Corner + building mass','Two canopies — fine grid']
def nums(s,key):return list(map(float,re.search(r'\b'+key+r'=([-+.\d,]+)',s)[1].rstrip(',').split(',')))
def cuboid(ax,b,color):
 x,X,y,Y,z,Z=b;v=np.array([[x,y,z],[X,y,z],[X,Y,z],[x,Y,z],[x,y,Z],[X,y,Z],[X,Y,Z],[x,Y,Z]])
 ax.add_collection3d(Poly3DCollection([v[i] for i in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]],facecolor=color,edgecolor='#5d6270',linewidth=.6,alpha=.9))
report=[]
for idx,(name,title) in enumerate(zip(NAMES,TITLES)):
 text=(ROOT/'decks'/f'{name}.fds').read_text();r=json.loads((ROOT/'data/cloud'/name/'result.json').read_text());assert hashlib.sha256(text.encode()).hexdigest()==r['deck_sha256']
 blocks=lambda typ:re.findall(r'&'+typ+r'\b.*?/',text,re.S)
 mesh=blocks('MESH')[0];domain=nums(mesh,'XB');ijk=nums(mesh,'IJK');dx=(domain[1]-domain[0])/ijk[0]
 obstacles=[nums(b,'XB') for b in blocks('OBST')];sources=[nums(b,'XB') for b in blocks('VENT') if "SURF_ID='IGNITOR'" in b]
 crowns=[]
 for b in blocks('INIT'):
  if "PART_ID='foliage'" in b:crowns.append((*nums(b,'XYZ'),nums(b,'RADIUS')[0],nums(b,'HEIGHT')[0]))
 direction=nums(blocks('WIND')[0],'DIRECTION')[0];angle=np.radians(270-direction);wind=np.array([np.cos(angle),np.sin(angle)])
 fig=plt.figure(figsize=(12,7.5),facecolor='#f4f7fb');ax=fig.add_axes([.02,.20,.55,.65],projection='3d');plan=fig.add_axes([.65,.24,.31,.54]);ax.set_facecolor('#f4f7fb')
 for b in obstacles:cuboid(ax,b,'#c4b199' if b[5]<=6 else '#9b9188')
 for i,(x,y,z,rad,h) in enumerate(crowns):
  theta=np.linspace(0,2*np.pi,45);zz=np.linspace(z,z+h,15);rr=rad*(1-(zz-z)/h)
  xx=x+rr[:,None]*np.cos(theta);yy=y+rr[:,None]*np.sin(theta);ax.plot_surface(xx,yy,np.broadcast_to(zz[:,None],xx.shape),color='#3a9460',alpha=.65,linewidth=0,shade=True)
  ax.text(x,y,z+h+1,f'{z+h:g} m top',fontsize=10,color='#246441',ha='center')
 for b in sources:cuboid(ax,[*b[:4],0,.08],'#e69c42')
 ax.quiver(3,5,1,wind[0]*4,wind[1]*4,0,color='#346eae',linewidth=2,arrow_length_ratio=.2);ax.text(3,5,2,'Wind 3 m/s',fontsize=9,color='#346eae')
 ax.set(xlim=(0,26),ylim=(4,23),zlim=(0,20),xlabel='x (m)',ylabel='y (m)',zlabel='Height (m)');ax.set_box_aspect((26,19,20));ax.view_init(elev=24,azim=-130)
 ax.set_title('Component view — same scale in all eight images',fontsize=10,pad=0)
 # Plan view includes full domain and makes changed buffers explicit.
 xmin,xmax,ymin,ymax,_,zmax=domain
 plan.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,fill=False,ls='--',lw=1.5,edgecolor='#657387'))
 for b in obstacles:plan.add_patch(Rectangle((b[0],b[2]),b[1]-b[0],b[3]-b[2],facecolor='#c4b199',edgecolor='#655b50',alpha=.65))
 for x,y,z,rad,h in crowns:plan.add_patch(Circle((x,y),rad,facecolor='#71b68a',edgecolor='#246441',alpha=.7))
 for b in sources:plan.add_patch(Rectangle((b[0],b[2]),b[1]-b[0],b[3]-b[2],facecolor='#e69c42',edgecolor='#ad6f1c'))
 plan.arrow(1,3,wind[0]*4,wind[1]*4,width=.12,head_width=.8,color='#346eae',length_includes_head=True)
 plan.set(xlim=(-10,34),ylim=(-10,34),xlabel='x (m)',ylabel='y (m)');plan.set_aspect('equal');plan.set_title('Plan: dashed line = full simulation boundary',fontsize=10);plan.grid(alpha=.15)
 fig.text(.035,.94,f'{idx+1}. {title}',fontsize=21,weight='bold',color='#1d3048');fig.text(.035,.895,f'{name}  |  cell {dx:g} m  |  domain {xmax-xmin:g} × {ymax-ymin:g} × {zmax:g} m  |  {int(np.prod(ijk)):,} cells',fontsize=11,color='#415975')
 status='Completed 180 s; no building ignition' if r['full_horizon'] else f'Incomplete: last device sample {r["physical_seconds_reached"]:.1f} s; runtime limit reached'
 fig.text(.035,.16,status,fontsize=12,weight='bold',color='#924b2f' if not r['full_horizon'] else '#334d66')
 fig.text(.035,.112,'Green = analytic particle-canopy envelope; tan = synthetic wood surfaces; orange = imposed ignition patch.',fontsize=10,color='#415975')
 fig.text(.035,.079,'Small canopy: base 3 m, top 10 m, diameter 4 m. Large: base 5 m, top 16 m, diameter 6 m.',fontsize=10,color='#415975')
 fig.text(.035,.046,'Facade: 8 m wide × 6 m tall. No trunks, terrain, windows, interiors or embers. Colours do not show heat.',fontsize=10,color='#415975')
 p=OUT/(name+'.png');fig.savefig(p,dpi=140);plt.close(fig)
 report.append(dict(case=name,deck_sha256=r['deck_sha256'],domain=domain,cell_m=dx,canopies=crowns,obstacles=obstacles,burners=sources))
for wave in (1,2):
 names=NAMES[(wave-1)*4:wave*4];thumbs=[Image.open(OUT/(n+'.png')).convert('RGB') for n in names];w,h=thumbs[0].size
 board=Image.new('RGB',(2*w,2*h+90),'#f4f7fb');d=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',42)
 d.text((45,20),f'Wave {wave} — executed component geometry (not a fire rendering)',font=font,fill='#1d3048')
 for i,im in enumerate(thumbs):board.paste(im,((i%2)*w,90+(i//2)*h))
 board.save(OUT/f'wave{wave}.png')
(OUT/'geometry-provenance.json').write_text(json.dumps(report,indent=2));print('Saved eight individual diagrams and two wave contact sheets')
