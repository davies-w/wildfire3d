"""Frozen single-canopy wind/ignition study. No cloud actions."""
import json,math,hashlib,re,copy
from pathlib import Path
from scipy.stats import qmc
import legacy_build as old
ROOT=Path(__file__).parent
CLASSES=old.CLASSES
MODELS={'A':old.MODELS['A']}
def templates():return {'A':old.templates()['A']}
def deck(c,ts):
 local=copy.deepcopy(ts)
 for i,p in enumerate(local['A']['heater']):
  angle=math.radians(c['angle_deg']-30+60*(i+.5)/1600)
  p['xyz']=[round(1.2*math.cos(angle),8),round(1.2*math.sin(angle),8),2.1]
 s,e=old.deck(c,local)
 s=s.replace('SPEED=3.',f"SPEED={c['wind_speed']:.8f}")
 s=s.replace('IJK=40,40,30, XB=0,20,0,20,0,15','IJK=48,32,32, XB=0,24,0,16,0,16')
 s=s.replace('XB=0,20,0,20,0,15','XB=0,24,0,16,0,16')
 s=re.sub(r"&DEVC ID='ground_.*?/",'',s)
 for x in range(1,24,2):
  for y in range(1,16,2):
   for suffix,q in [('T','WALL TEMPERATURE'),('Q','NET HEAT FLUX')]:
    s=s.replace('&TAIL /',f"&DEVC ID='ground_{x}_{y}_{suffix}', XYZ={x},{y},0, IOR=3, QUANTITY='{q}' /\n&TAIL /")
 s=s.replace('&TAIL /',"&SLCF XB=0,24,0,16,0,16, QUANTITY='INTEGRATED INTENSITY', CELL_CENTERED=T /\n&TAIL /")
 if c['split']!='pilot':s=s.replace('DT_SLCF=2.,','DT_SLCF=2., DT_SL3D=2.,')
 if c.get('expanded'):s=s.replace('IJK=48,32,32, XB=0,24,0,16,0,16','IJK=64,48,48, XB=-4,28,-4,20,0,24')
 return s,e

def main():
 assert not (ROOT/'budget.json').exists()
 ts=templates();(ROOT/'data/tree-templates.json').write_text(json.dumps(ts,indent=2)+'\n')
 rows=[]
 def case(name,split,w,a,**kw):
  c=dict(case='s27_'+name,family='single',split=split,trees=[dict(type='A',x=8.,y=8.)],heater_type='A',heater_xy=[8.,8.],strength=1.,duration=20,wind_speed=float(w),angle_deg=float(a),horizon_s=180,variant='passive',profile=False,solve_limit_s=1500,dx=.5,**kw)
  s,_=deck(c,ts);c['deck_sha256']=hashlib.sha256(s.encode()).hexdigest();(ROOT/'decks'/(c['case']+'.fds')).write_text(s);rows.append(c)
 for i,(w,a) in enumerate([(1,0),(1,180),(5,0),(5,180)]):case('pilot_'+str(i),'pilot',w,a)
 for i,(w,a) in enumerate([(1,0),(5,180)]):case('domain_'+str(i),'domain',w,a,expanded=True)
 for split,n,seed in [('train',32,2701),('validation',6,2702),('test',6,2703)]:
  points=qmc.Sobol(2,scramble=True,seed=seed).random_base2(5 if n==32 else 3)[:n]
  for i,(u,v) in enumerate(points):case(split+'_'+str(i),split,1+4*u,360*v,training_rank=i)
 (ROOT/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
 freeze=dict(template_sha256=hashlib.sha256((ROOT/'data/tree-templates.json').read_bytes()).hexdigest(),cases={c['case']:c['deck_sha256'] for c in rows},rule='Frozen A particles and weights. Only wind and heater arc angle vary; expanded-domain controls explicit.')
 (ROOT/'results/input-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print('Prepared',len(rows),'cases')
if __name__=='__main__':main()
