"""Check all four main-structure walls around the first long-run ignition event."""
import os,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;case='lot_full';folder=ROOT/'data/cloud'/case
binary=Path(os.environ.get('FDS2ASCII') or str(ROOT.parents[1]/'FDS/install/bin/fds2ascii'))
dest=ROOT/'data/long-boundary';dest.mkdir(parents=True,exist_ok=True);records=[]
for orientation,axis,position,label in [(-1,0,18,'west'),(1,0,30,'east'),(-2,1,8,'south'),(2,1,16,'north')]:
 for index,quantity in [(1,'WALL TEMPERATURE'),(2,'BURNING RATE')]:
  out=dest/f'{label}-{index}-210-225.csv'
  if not out.exists():
   answers=f'{case}\n3\n1\nn\n210.0 225.0\n{orientation}\n1\n{index}\n{out}\n'
   p=subprocess.run([str(binary)],cwd=folder,input=answers,capture_output=True,text=True,check=True,timeout=60)
   out.with_suffix('.log').write_text(p.stdout+p.stderr)
  values=[]
  for line in out.read_text().splitlines():
   try:
    r=list(map(float,line.split(',')))
    if len(r)==4 and abs(r[axis]-position)<1e-5 and 18<=r[0]<=30 and 8<=r[1]<=16 and 0<=r[2]<=3.5:values.append(r[3])
   except ValueError:pass
  if not values:raise RuntimeError('Missing wall: '+label)
  records.append(dict(wall=label,quantity=quantity,min=min(values),max=max(values),positive_samples=sum(v>0 for v in values),samples=len(values)))
result=dict(case=case,averaging_window_s=[210,225],note='Coordinates select the four main house walls, including inert windows; roof overhang is outside these planes. Temperature units C; burning rate kg/m2/s.',walls=records)
(ROOT/'results/long-boundary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
