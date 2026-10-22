"""Small local-configuration development manifest and instrumented decks; no cloud launch."""
import hashlib,json,re
from scene import ROOT,CLASSES

def manifest():
 rows=[]
 for family in ['single','transfer','combined','corner']:
  for i,(gap,wind,moisture) in enumerate([(1,3,.14),(3,2,.08),(6,4,.20)]):
   rows.append(dict(case=f'b21_{family}_{i}',split='train',family=family,gap_m=gap,wind_m_s=wind,direction=270 if i!=2 else 225,moisture=moisture,receiver_large=family=='transfer' and i==1))
 for family in ['single','transfer','combined','corner']:
  rows.append(dict(case=f'b21_{family}_validation',split='validation',family=family,gap_m=2,wind_m_s=3,direction=270,moisture=.11,receiver_large=family=='transfer'))
 rows.append(dict(case="b21_transfer_hot",split="train",family="transfer",gap_m=.5,wind_m_s=6,direction=270,moisture=.08,receiver_large=True))
 return rows

def build(c):
 s=(ROOT/'decks/overnight21_stronger.fds').read_text();s=s.replace("CHID='overnight21_stronger'",f"CHID='{c['case']}'").replace('IJK=48,48,48, XB=0,24,0,24,0,24','IJK=64,48,48, XB=0,32,0,24,0,24')
 s=s.replace('SPEED=3., DIRECTION=270.','SPEED='+str(c['wind_m_s'])+', DIRECTION='+str(c['direction'])+'.')
 s=re.sub(r'MOISTURE_CONTENT\s*=\s*0\.14','MOISTURE_CONTENT = '+str(c['moisture']),s)
 s=re.sub(r'&INIT\b.*?/','',s,flags=re.S)
 # Replace class output lists with explicitly distinct incoming radiation and convection.
 def particle(m):
  b=m[0]
  if "ID='contact ignitor'" in b:return b
  return re.sub(r'QUANTITIES=.*?(?=, STATIC)',"QUANTITIES='PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX'",b,flags=re.S)
 s=re.sub(r'&PART\b.*?/',particle,s,flags=re.S)
 s=re.sub(r'&DEVC\b.*?/',lambda m:'' if any(x in m[0] for x in ["ID='mass ","ID='small ","ID='large ","ID='fuel_release "]) else m[0],s,flags=re.S)
 s=s.replace('XB=16,16.5,8,16,0,6','XB=24,24.5,8,16,0,6').replace('XB=15,25,7,17,0,7','XB=23,31,7,17,0,7').replace('XYZ=16.,','XYZ=24.,').replace('XYZ=16,','XYZ=24,')
 s=s.replace('DT_PART=1.','DT_PART=.5')
 gap=c['gap_m'];family=c['family'];nodes=[]
 def node(x,y,r=2,h=7,z=3,seed=True):nodes.append(dict(id=f'v{len(nodes)}',x=x,y=y,base=z,height=h,radius=r,initialized=seed))
 if family in ['single','corner']:node(24-2-gap,12)
 elif family=='combined':node(24-2-gap,9);node(24-2-gap,15)
 else:
  rr=3 if c['receiver_large'] else 2
  node(19-rr-2-gap,12);node(19,12,r=rr,h=11 if rr==3 else 7,z=5 if rr==3 else 3,seed=False)
 extra=[]
 if family=='corner':extra.append("&OBST XB=24,30,16,16.5,0,6, SURF_ID='HOUSE', BNDF_OBST=T /")
 for n in nodes:
  x,y,z,h,r=[n[k] for k in ['x','y','base','height','radius']];box=f'{x-r},{x+r},{y-r},{y+r},{z},{z+h}'
  for fuel,density in CLASSES:
   extra.append(f"&INIT PART_ID='{fuel}', XYZ={x},{y},{z}, RADIUS={r}, HEIGHT={h}, SHAPE='CONE', N_PARTICLES_PER_CELL=1, DRY=T, MASS_PER_VOLUME={density} /")
   extra.append(f"&DEVC ID='{n['id']} mass {fuel}', QUANTITY='MPUV', PART_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='VOLUME INTEGRAL' /")
   extra.append(f"&DEVC ID='{n['id']} fuel {fuel}', QUANTITY='MASS FLUX', SPEC_ID='FUEL VAPOR', PART_ID='{fuel}', SURF_ID='{fuel}', XB={box}, SPATIAL_STATISTIC='SURFACE INTEGRAL' /")
  if n['initialized']:extra.append(f"&INIT PART_ID='contact ignitor', XYZ={x},{y},{z+.1}, RADIUS={r*.75}, SHAPE='RING', N_PARTICLES=1600 /")
 s=s.replace('&TAIL /','\n'.join(extra)+'\n&TAIL /')
 return s,dict(c,canopies=nodes,facade=dict(x=24,y=[8,16],z=[0,6],thermal_thickness_m=.02),domain_m=[0,32,0,24,0,24],dx_m=.5,horizon_s=90,allowance_usd=.25,max_vm_hours=2,deck_sha256=hashlib.sha256(s.encode()).hexdigest())

def prepare():
 ledger=ROOT/'budget-overnight.json'
 if ledger.exists():
  reserved=json.loads(ledger.read_text()).get('reservations',{})
  assert not any(c['case'] in reserved for c in manifest()), 'Cannot regenerate a campaign with reserved cases; edit unlaunched cases individually.'
 rows=[]
 for c in manifest():
  s,r=build(c);(ROOT/'decks'/f"{c['case']}.fds").write_text(s);rows.append(r)
 (ROOT/'component-development.json').write_text(json.dumps(dict(status='prepared_not_submitted',cases=rows,allowance_usd=4.25,scope='13 training plus4 geometry-held-out validation configurations,90s, generic10/16m canopy patches and synthetic wood facade. Not a calibrated physical reference.',state_interface='Vegetation per-class temperature distributions, mass, emitted fuel and measured incoming radiation/convection; facade patch temperatures, heating and ignition. Inputs at inference are geometry/materials/wind/moisture and prescribed initialization only.',confounding='Gap, wind and moisture co-vary in this tiny pilot; no independent sensitivities can be claimed. Validation holds whole configurations, not time rows. Cold initial states with prescribed20s heating pulses, not pre-burned canopy states.',test_templates=['santa_rosa_east_03','glen_ellen_06'],test_rule='Exact larger-scene geometry must be frozen before model selection; predictions and model hashes frozen before accessing any held-out FDS output.'),indent=2))
 from add_component_roof_coverage import upgrade
 upgrade()
 print('Prepared',len(rows),'development decks; no cloud submission')
if __name__=='__main__':prepare()
