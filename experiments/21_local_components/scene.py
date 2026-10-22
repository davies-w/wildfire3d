"""Explicit Stage A analytic canopy patches and synthetic facade assemblies."""
import json,re,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CLASSES=[('foliage',1.683),('small roundwood',.289),('medium roundwood',.263),('large roundwood',.394)]
def cases():
 return [dict(case='a21_single',kind='single',direction=270),dict(case='a21_double',kind='double',direction=270),dict(case='a21_corner',kind='corner',direction=225),dict(case='a21_bare',kind='bare',direction=270)]
def deck(c,horizon=180):
 kind=c['kind'];dx=c.get('dx',.5);expanded=c.get('expanded',False)
 box=(-8,32,-8,32,0,32) if expanded else (0,24,0,24,0,24)
 ijk=[round((box[i+1]-box[i])/dx) for i in (0,2,4)]
 s=[f"&HEAD CHID='{c['case']}', TITLE='Stage A assigned canopy patches and synthetic wood facade' /",f"&MESH IJK={','.join(map(str,ijk))}, XB={','.join(map(str,box))} /",f'&TIME T_END={horizon} /',"&MISC RND_SEED=4321, BNDF_DEFAULT=F /",f"&WIND SPEED=3., DIRECTION={c['direction']}. /",(ROOT/'inputs/vegetation_model.txt').read_text()]
 src=(ROOT/'inputs/tree_2_m_14_pc.fds').read_text();s.append(src[src.index("&SURF ID                        = 'foliage'"):src.index('&CATF')])
 s += [b for b in re.findall(r'&PART\b.*?/',src,re.S) if "ID='ignitor'" not in b]
 crowns=[(11,12,3,7,2)]
 if kind=='double':crowns.append((8,18,5,11,3))
 if kind!='bare':
  for x,y,z,h,r in crowns:
   for fuel,density in CLASSES:s.append(f"&INIT PART_ID='{fuel}', XYZ={x},{y},{z}, RADIUS={r}, HEIGHT={h}, SHAPE='CONE', N_PARTICLES_PER_CELL=1, DRY=T, MASS_PER_VOLUME={density} /")
 s += ["&MATL ID='wall wood', DENSITY=500., CONDUCTIVITY=.12, SPECIFIC_HEAT=1.7 /","&SURF ID='HOUSE', MATL_ID='wall wood', THICKNESS=.02, HRRPUA=200., IGNITION_TEMPERATURE=350., TAU_Q=1. /", "&OBST XB=16,16.5,8,16,0,6, SURF_ID='HOUSE', BNDF_OBST=T /"]
 if kind=='corner':s += ["&OBST XB=16,22,16,16.5,0,6, SURF_ID='HOUSE', BNDF_OBST=T /","&OBST XB=15.5,22,7.5,16.5,6,6.5, SURF_ID='HOUSE', BNDF_OBST=T /"]
 if expanded:s += ["&OBST XB=16.5,24,8,16,0,6, SURF_ID='HOUSE', BNDF_OBST=T /"]
 s += ["&SURF ID='IGNITOR', HRRPUA=1000., RAMP_Q='source' /","&RAMP ID='source', T=0., F=0. /","&RAMP ID='source', T=2., F=1. /","&RAMP ID='source', T=20., F=1. /","&RAMP ID='source', T=21., F=0. /"]
 for x,y,*_ in crowns:s.append(f"&VENT XB={x-1},{x+1},{y-1},{y+1},0,0, SURF_ID='IGNITOR' /")
 s += [f"&VENT MB='{v}', SURF_ID='OPEN' /" for v in ('XMIN','XMAX','YMIN','YMAX','ZMAX')]
 quantities=['WALL TEMPERATURE','INCIDENT HEAT FLUX','CONVECTIVE HEAT FLUX','RADIATIVE HEAT FLUX','BURNING RATE']
 for q in quantities:s.append(f"&BNDF QUANTITY='{q}' /")
 for name,q in [('house_max','WALL TEMPERATURE'),('house_burn_max','BURNING RATE')]:s.append(f"&DEVC ID='{name}', QUANTITY='{q}', SURF_ID='HOUSE', XB=15,25,7,17,0,7, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /")
 # Fixed physical patch centres align across both grids; do not compare changing maxima.
 for y in (8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5):
  for z in (.5,1.5,2.5,3.5,4.5,5.5):
   for name,q in [('temp','WALL TEMPERATURE'),('rad_in','INCIDENT HEAT FLUX'),('conv','CONVECTIVE HEAT FLUX'),('burn','BURNING RATE')]:s.append(f"&DEVC ID='p{y}_{z}_{name}', XYZ=16.,{y},{z}, IOR=-1, QUANTITY='{q}' /")
 for depth in (.005,.01,.015):s.append(f"&DEVC ID='wall_depth_{depth}', XYZ=16,12.5,2.5, IOR=-1, QUANTITY='INSIDE WALL TEMPERATURE', DEPTH={depth} /")
 for fuel,_ in CLASSES:s.append(f"&DEVC ID='mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB=0,24,0,24,0,24, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
 for q in ('TEMPERATURE','VELOCITY'):s.append(f"&SLCF PBY=12., QUANTITY='{q}' /")
 s += ["&DUMP DT_DEVC=.5, DT_HRR=.5, DT_BNDF=2., DT_SLCF=2., DT_PART=5., DT_RESTART=100000., SMOKE3D=F /",'&TAIL /']
 text='\n'.join(s)+'\n';record=dict(c,cells=math.prod(ijk),domain_m=box,dx_m=dx,horizon_s=horizon,variant='passive',profile=False,source_kw=4000*len(crowns),source_energy_kj=4000*len(crowns)*19.5,nominal_dry_fuel_kg=0 if kind=='bare' else sum(math.pi*r*r*h/3*sum(v for _,v in CLASSES) for _,_,_,h,r in crowns),canopy_patches=[] if kind=='bare' else crowns,deck_sha256=hashlib.sha256(text.encode()).hexdigest())
 return text,record
if __name__=='__main__':
 (ROOT/'decks').mkdir(exist_ok=True);records=[]
 for c in cases():
  s,r=deck(c);(ROOT/'decks'/f"{c['case']}.fds").write_text(s);records.append(r)
 (ROOT/'wave1.json').write_text(json.dumps(records,indent=2)+'\n')
 print([(r['case'],r['cells'],r['nominal_dry_fuel_kg']) for r in records])
