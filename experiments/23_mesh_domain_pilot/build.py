import json,re,hashlib,math
from pathlib import Path
ROOT=Path(__file__).parent
base=(ROOT/'base-input.fds').read_text()
CLASSES=[('foliage',1.683),('small roundwood',.289),('medium roundwood',.263),('large roundwood',.394)]
def build(layout,xy,dx,expanded):
 name=f'p23_{layout}_{"expanded" if expanded else "compact"}_{str(dx).replace(".","p")}'
 lo,hi,top=(-6,26,24) if expanded else (0,20,15)
 s=base.replace('BNDF_DEFAULT=F','BNDF_DEFAULT=T')
 for tag in ['HEAD','MESH','TIME','INIT','OBST','VENT','DEVC','SLCF','DUMP','TAIL']:
  s=re.sub(r'&'+tag+r'\b.*?/','',s,flags=re.S)
 s=s.replace('MOISTURE_CONTENT         = 0.14','MOISTURE_CONTENT         = 0.12')
 s=s.replace("QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS'", "QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR'")
 a=[f"&HEAD CHID='{name}', TITLE='Uniform resolution and air-volume fidelity comparison' /",f'&MESH IJK={int((hi-lo)/dx)},{int((hi-lo)/dx)},{int(top/dx)}, XB={lo},{hi},{lo},{hi},0,{top} /','&TIME T_END=180 /',s]
 a.extend(["&MATL ID='generic soil', DENSITY=1500., CONDUCTIVITY=1., SPECIFIC_HEAT=1.2 /","&SURF ID='GROUND', MATL_ID='generic soil', THICKNESS=.5, BACKING='INSULATED' /", "&OBST XB=11,17,8,14,0,5, SURF_ID='HOUSE', BNDF_OBST=T /", "&VENT MB='ZMIN', SURF_ID='GROUND' /"])
 for mb in ['XMIN','XMAX','YMIN','YMAX','ZMAX']:a.append(f"&VENT MB='{mb}', SURF_ID='OPEN' /")
 for index,(x,y,h) in enumerate([(5,6,8),(*xy,6)]):
  box=f'{x-2},{x+2},{y-2},{y+2},2,{2+h}'
  for fuel,density in CLASSES:
   
   for pt in json.loads((ROOT/'data/fixed-particles.json').read_text())[fuel][index*400:(index+1)*400]:
    px,py,pz=pt['xyz'];px+=x-(5 if index==0 else 6);py+=y-(6 if index==0 else 12)
    a.append(f"&INIT PART_ID='{fuel}', XYZ={px:.8f},{py:.8f},{pz:.8f}, SHAPE='LINE', N_PARTICLES=1, PARTICLE_WEIGHT_FACTOR={pt['weight']:.10g} /")
   a.append(f"&DEVC ID='c{index} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
   a.append(f"&DEVC ID='c{index} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /")
 a.append("&INIT PART_ID='contact ignitor', XYZ=5,6,2.1, RADIUS=1.5, SHAPE='RING', N_PARTICLES=1600, UNIFORM=T /")
 # Actual native face-cell centres; fine fields can be area-aggregated onto common1m patches.
 patches=[]
 for axis,face,normal,bounds in [('x',11,-1,(8,14,0,5)),('x',17,1,(8,14,0,5)),('y',8,-2,(11,17,0,5)),('y',14,2,(11,17,0,5)),('z',5,3,(11,17,8,14))]:
  u0,u1,v0,v1=bounds
  for i in range(round((u1-u0)/dx)):
   for j in range(round((v1-v0)/dx)):
    u,v=u0+(i+.5)*dx,v0+(j+.5)*dx
    xyz=(face,u,v) if axis=='x' else ((u,face,v) if axis=='y' else (u,v,face))
    pid=f'{axis}{face}_{i}_{j}';patches.append(dict(id=pid,xyz=xyz,ior=normal,area_m2=dx*dx))
    for suffix,q in [('T','WALL TEMPERATURE'),('R','INCIDENT HEAT FLUX'),('C','CONVECTIVE HEAT FLUX')]:
     a.append(f"&DEVC ID='{pid}_{suffix}', XYZ={','.join(map(str,xyz))}, IOR={normal}, QUANTITY='{q}', TEMPORAL_STATISTIC='INSTANT VALUE' /")
 for q in ['TEMPERATURE','HRRPUV','U-VELOCITY','V-VELOCITY','W-VELOCITY']:a.append(f"&SLCF XB=0,20,0,20,0,15, QUANTITY='{q}', CELL_CENTERED=T /")
 a.extend(['&DUMP DT_DEVC=1., DT_HRR=1., DT_BNDF=2., DT_SLCF=2., DT_PART=2., DT_RESTART=30., SMOKE3D=F /','&TAIL /'])
 text='\n'.join(a)+'\n'
 (ROOT/'decks'/f'{name}.fds').write_text(text)
 return dict(case=name,layout=layout,dx=dx,expanded=expanded,horizon_s=180,variant='passive',profile=False,deck_sha256=hashlib.sha256(text.encode()).hexdigest(),patches=patches,solve_limit_s=2700 if expanded and dx==.5 else (900 if dx==.5 else 600))
if __name__=='__main__':
 assert not (ROOT/'budget.json').exists(),'No regeneration after reservation'
 for d in ['decks','results','jobs','data/preflight','data/cloud','data/downloads']:(ROOT/d).mkdir(parents=True,exist_ok=True)
 rows=[build(k,xy,dx,ex) for k,xy in zip('ABC',[(6,12),(5,11),(7,15)]) for dx in [1,.5] for ex in [False,True]]
 (ROOT/'cases.json').write_text(json.dumps(rows,indent=2))
 print('Prepared',len(rows),'uniform-grid cases')
