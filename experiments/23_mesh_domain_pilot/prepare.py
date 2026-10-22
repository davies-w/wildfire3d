import json
from pathlib import Path
p=Path(__file__).parent
variants=[]
for name,xb in [('compact',[0,20,0,20,0,15]),('expanded',[-6,26,-6,26,0,24])]:
    volume=(xb[1]-xb[0])*(xb[3]-xb[2])*xb[5]
    for dx in [1,.5,.25,'mixed']:
        count=196608+(volume-3072)/.125 if dx=='mixed' else volume/dx**3
        variants.append(dict(domain=name,xb=xb,spacing_m=dx,cells=int(count)))
layouts=[dict(id=i,source_xy=[5,6],receiver_xy=xy) for i,xy in zip('ABC',[[6,12],[5,11],[7,15]])]
plan=dict(status='PROPOSED_NOT_RUN',horizon_s=180,wind_toward='+x',wind_speed_m_s=3,moisture_dry_basis=.12,building_xb=[11,17,8,14,0,5],source_crown=dict(radius=2,base=2,top=10),receiver_crown=dict(radius=2,base=2,top=8),fine_region_xb=[2,18,2,18,0,12],layouts=layouts,variants=variants,total_cases=24)
(p/'data').mkdir(exist_ok=True)
(p/'data/plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(p/'data/pilot.html').write_text((p/'pilot.template.html').read_text())
assert len(variants)*len(layouts)==24
for l in layouts:
    a,b=l['receiver_xy'];assert ((a-5)**2+(b-6)**2)**.5>=4.5
print('24 proposed comparisons; no solver decks or jobs generated.')
