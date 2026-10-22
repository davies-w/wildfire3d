"""Prepare only unreserved corner configurations with measured roof/return surfaces."""
import hashlib,json,re
from pathlib import Path
from scene import ROOT

def upgrade():
 p=ROOT/'component-development.json';doc=json.loads(p.read_text());ledger=json.loads((ROOT/'budget-overnight.json').read_text())
 for c in doc['cases']:
  if c['family']!='corner':continue
  assert c['case'] not in ledger['reservations'], 'Never alter a reserved input'
  deck=ROOT/'decks'/f"{c['case']}.fds";s=deck.read_text()
  if c.get('extra_surface_patches'):continue
  extra=["&OBST XB=22,28,8,16,6,6.5, SURF_ID='HOUSE', BNDF_OBST=T /"]
  patches=[]
  def probe(x,y,z,normal,ior):
   stem=f'q{len(patches)}';patches.append(dict(id=stem,xyz=[x,y,z],normal=normal))
   for suffix,quantity in [('temp','WALL TEMPERATURE'),('rad_in','INCIDENT HEAT FLUX'),('conv','CONVECTIVE HEAT FLUX'),('burn','BURNING RATE')]:extra.append(f"&DEVC ID='{stem}_{suffix}', XYZ={x},{y},{z}, IOR={ior}, QUANTITY='{quantity}' /")
  for x in [22.5,23.5,24.5,25.5,26.5,27.5]:
   for y in [8.5+i for i in range(8)]:
    probe(x,y,6.5,[0,0,1],3)
    if x!=24.5:probe(x,y,6,[0,0,-1],-3)
  for x in [24.5+i for i in range(6)]:
   for z in [.5+i for i in range(6)]:
    probe(x,16,z,[0,-1,0],-2);probe(x,16.5,z,[0,1,0],2)
  s=s.replace('&TAIL /','\n'.join(extra)+'\n&TAIL /');deck.write_text(s)
  c['extra_surface_patches']=patches;c['roof_box_m']=[22,28,8,16,6,6.5];c['deck_sha256']=hashlib.sha256(s.encode()).hexdigest();c['coverage_note']='Added synthetic flat 20mm wood roof,2m front overhang,top/underside and return-wall probes. All wall/roof material identical, not realistic roof assembly.'
 doc['scope']=doc['scope'].replace('12 training','13 training');p.write_text(json.dumps(doc,indent=2))
if __name__=='__main__':upgrade()
