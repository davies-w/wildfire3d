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

def deck(name,layout,power,horizon=HORIZON,seed=1234):
    mode="full"
    anchors=json.loads((ROOT/"design.json").read_text())["anchors_m"]
    centers=[anchors[a] for a in layout]
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
    for x,y in centers:
        for fuel,density in classes:
            lines.append(f"&INIT PART_ID='{fuel}', XYZ={x},{y},0.15, RADIUS=0.85, HEIGHT=1.96, SHAPE='CONE', N_PARTICLES_PER_CELL=1, DRY=T, MASS_PER_VOLUME={density} /")
    lines += ["&MATL ID='wall wood', DENSITY=500., CONDUCTIVITY=.12, SPECIFIC_HEAT=1.7 /",
      "&SURF ID='HOUSE', MATL_ID='wall wood', THICKNESS=.02, HRRPUA=200., IGNITION_TEMPERATURE=350., TAU_Q=1. /",
      "&OBST XB=14,20,10,14,0,4, SURF_ID='HOUSE', BNDF_OBST=T /",
      f"&SURF ID='IGNITOR', HRRPUA={power/len(centers)}, RAMP_Q='source' /",
      "&RAMP ID='source', T=0., F=0. /","&RAMP ID='source', T=2., F=1. /",
      "&RAMP ID='source', T=30., F=1. /","&RAMP ID='source', T=31., F=0. /",
      ]
    for x,y in centers:
        lines.append(f"&VENT XB={x-.5},{x+.5},{y-.5},{y+.5},0,0, SURF_ID='IGNITOR' /")
    lines += [f"&VENT MB='{side}', SURF_ID='OPEN' /" for side in ['XMIN','XMAX','YMIN','YMAX','ZMAX']]
    for ident,q in [('house_max','WALL TEMPERATURE'),('house_flux_max','GAUGE HEAT FLUX'),('house_burn_max','BURNING RATE')]:
        lines.append(f"&DEVC ID='{ident}', QUANTITY='{q}', SURF_ID='HOUSE', XB=13,21,9,15,0,5, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /")
    face_boxes={
      'west':(13.9,14.1,10.1,13.9,.1,3.9),
      'east':(19.9,20.1,10.1,13.9,.1,3.9),
      'south':(14.1,19.9,9.9,10.1,.1,3.9),
      'north':(14.1,19.9,13.9,14.1,.1,3.9),
      'roof':(14.1,19.9,10.1,13.9,3.9,4.1)}
    for face,box in face_boxes.items():
        for suffix,q in [('temp','WALL TEMPERATURE'),('flux','GAUGE HEAT FLUX')]:
            lines.append(f"&DEVC ID='{face}_{suffix}', QUANTITY='{q}', SURF_ID='HOUSE', XB={','.join(map(str,box))}, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /")
    for fuel,_ in classes:
        lines.append(f"&DEVC ID='mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB=0,24,0,24,0,12, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
    for q in ['WALL TEMPERATURE','GAUGE HEAT FLUX','BURNING RATE']:lines.append(f"&BNDF QUANTITY='{q}' /")
    lines += ["&DUMP DT_DEVC=.5, DT_HRR=.5, DT_BNDF=2., DT_PART=30., DT_RESTART=100000., SMOKE3D=F /","&TAIL /"]
    return '\n'.join(lines)+'\n'
def write(name,layout,power,horizon=HORIZON,seed=1234,split='calibration'):
    assert set(layout)<=set('ABCD') and len(layout)==len(set(layout))
    s=deck(name,layout,power,horizon,seed)
    (ROOT/'decks').mkdir(exist_ok=True)
    (ROOT/'decks'/f'{name}.fds').write_text(s)
    return dict(case=name,layout=layout,split=split,total_source_kw=power,horizon_s=horizon,seed=seed,cells=55296,profile=False,variant='passive',deck_sha256=hashlib.sha256(s.encode()).hexdigest())

if __name__=='__main__':
    design=json.loads((ROOT/'design.json').read_text())
    for row in design['cases']:
        write(row['case'].replace('.','p'),row['layout'],800*row['total_source_power_factor'],split=row['split'])
    print('Generated 42 preview decks at provisional P0=800 kW; cloud worker uses calibrated P0.')
