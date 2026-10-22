"""Fixed physical scene; only surrounding mesh/domain and source strength vary."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
HORIZON=90.
# Core is identical, fine and particle-seeded identically in every variant.
CORE=(8,22,8,16,0,6)
DOMAINS={'full':(0,24,0,24,0,12),'wide':(0,24,6,18,0,12),'tight':(4,24,6,18,0,8),'mixed':(0,24,0,24,0,12),'combined':(4,24,6,18,0,8)}
def mesh_boxes(mode):
    a,b,c,d,e,f=DOMAINS[mode];u,v,w,x,y,z=CORE
    boxes=[(CORE,.5),((a,u,c,d,e,f),2 if mode in ('mixed','combined') else .5),((v,b,c,d,e,f),2 if mode in ('mixed','combined') else .5),((u,v,c,w,e,f),2 if mode in ('mixed','combined') else .5),((u,v,x,d,e,f),2 if mode in ('mixed','combined') else .5),((u,v,w,x,z,f),2 if mode in ('mixed','combined') else .5)]
    return [(box,max(step for step in (.5,1.,2.) if step<=dx and all((box[j+1]-box[j])/step>=4 for j in (0,2,4)))) for box,dx in boxes]

def deck(name,mode,power,horizon=HORIZON,seed=1234):
    lines=[f"&HEAD CHID='{name}', TITLE='Particle vegetation domain study: {mode}' /"]
    for i,(box,dx) in enumerate(mesh_boxes(mode)):
        ijk=[int(round((box[j+1]-box[j])/dx)) for j in (0,2,4)]
        assert all(n>0 for n in ijk)
        lines.append(f"&MESH ID='mesh{i}', CHECK_MESH_ALIGNMENT=T, IJK={','.join(map(str,ijk))}, XB={','.join(map(str,box))} /")
    lines += [f'&TIME T_END={horizon} /',f'&MISC RND_SEED={seed}, BNDF_DEFAULT=F /',"&WIND SPEED=3., DIRECTION=270. /",(ROOT/'inputs/vegetation_model.txt').read_text()]
    source=(ROOT/'inputs/tree_2_m_14_pc.fds').read_text()
    # Copy the four validated fuel-element definitions; keep their dry fuel load and moisture.
    start=source.index("&SURF ID                        = 'foliage'")
    end=source.index('&CATF')
    lines.append(source[start:end])
    import re
    for block in re.findall(r'&PART\b.*?/',source,re.S):
        if "ID='ignitor'" not in block:lines.append(block)
    classes=[('foliage',1.683),('small roundwood',.289),('medium roundwood',.263),('large roundwood',.394)]
    # Two actual conical particle crowns, including an off-axis source of heat.
    for x,y in [(12.,12.),(11.,9.)]:
        for fuel,density in classes:
            lines.append(f"&INIT PART_ID='{fuel}', XYZ={x},{y},0.15, RADIUS=0.85, HEIGHT=1.96, SHAPE='CONE', N_PARTICLES_PER_CELL=1, DRY=T, MASS_PER_VOLUME={density} /")
    lines += ["&MATL ID='wall wood', DENSITY=500., CONDUCTIVITY=.12, SPECIFIC_HEAT=1.7 /",
      "&SURF ID='HOUSE', MATL_ID='wall wood', THICKNESS=.02, HRRPUA=200., IGNITION_TEMPERATURE=350., TAU_Q=1. /",
      "&OBST XB=14,20,10,14,0,4, SURF_ID='HOUSE', BNDF_OBST=T /",
      f"&SURF ID='IGNITOR', HRRPUA={power}, RAMP_Q='source' /",
      "&RAMP ID='source', T=0., F=0. /","&RAMP ID='source', T=2., F=1. /",
      "&RAMP ID='source', T=30., F=1. /","&RAMP ID='source', T=31., F=0. /",
      "&VENT XB=11.5,12.5,11.5,12.5,0,0, SURF_ID='IGNITOR' /",
      "&VENT XB=10.5,11.5,8.5,9.5,0,0, SURF_ID='IGNITOR' /"]
    lines += [f"&VENT MB='{side}', SURF_ID='OPEN' /" for side in ['XMIN','XMAX','YMIN','YMAX','ZMAX']]
    for ident,q in [('house_max','WALL TEMPERATURE'),('house_flux_max','GAUGE HEAT FLUX'),('house_burn_max','BURNING RATE')]:
        lines.append(f"&DEVC ID='{ident}', QUANTITY='{q}', SURF_ID='HOUSE', XB=13,21,9,15,0,5, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /")
    for fuel,_ in classes:
        lines.append(f"&DEVC ID='mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB=8,22,8,16,0,6, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
    for q in ['WALL TEMPERATURE','GAUGE HEAT FLUX','BURNING RATE']:lines.append(f"&BNDF QUANTITY='{q}' /")
    lines += ["&DUMP DT_DEVC=.5, DT_HRR=.5, DT_BNDF=2., DT_PART=30., DT_RESTART=100000., SMOKE3D=F /","&TAIL /"]
    return '\n'.join(lines)+'\n'
def write(name,mode,power,horizon=HORIZON,seed=1234):
    s=deck(name,mode,power,horizon,seed);(ROOT/'decks').mkdir(exist_ok=True);(ROOT/'decks'/f'{name}.fds').write_text(s)
    cells=sum(round((b[1]-b[0])*(b[3]-b[2])*(b[5]-b[4])/dx**3) for b,dx in mesh_boxes(mode))
    return dict(case=name,mode=mode,power_kw_m2=power,horizon_s=horizon,seed=seed,cells=cells,profile=False,variant='passive',deck_sha256=hashlib.sha256(s.encode()).hexdigest())
if __name__=='__main__':
    rows=[write('preflight_'+mode,mode,1000,.05) for mode in DOMAINS]
    (ROOT/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
