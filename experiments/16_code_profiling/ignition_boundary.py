"""Check main-structure west-face burning rate directly in raw boundary files."""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
binary=Path(os.environ.get('FDS2ASCII') or str(ROOT.parents[1]/'FDS/install/bin/fds2ascii'))
outdir=ROOT/'data/ignition-boundary';outdir.mkdir(parents=True,exist_ok=True)
records=[]
for case in ('hot_a','hot_coarse','hot_radiation','hot_passive'):
 start,end=20,30
 folder=ROOT/'data/cloud'/case
 if not (folder/'result.json').exists():continue
 out=outdir/(case+'.csv')
 if not out.exists():
  answers=f'{case}\n3\n1\nn\n{start}.0 {end}.0\n-1\n1\n2\n{out}\n'
  p=subprocess.run([str(binary)],cwd=folder,input=answers,text=True,capture_output=True,check=True,timeout=60)
  (outdir/(case+'.log')).write_text(p.stdout+p.stderr)
 values=[]
 for line in out.read_text().splitlines():
  try:
   row=list(map(float,line.split(',')))
   if len(row)==4 and abs(row[0]-18)<1e-5 and 8<=row[1]<=16 and 0<=row[2]<=3.5:values.append(row[3])
  except ValueError:pass
 if not values:raise RuntimeError('Missing boundary data')
 records.append(dict(case=case,averaging_window_s=[start,end],min=min(values),max=max(values),positive_samples=sum(v>0 for v in values),samples=len(values)))
result=dict(quantity='BURNING RATE',units='kg/m2/s',surface='West plane x=18,y=8..16,z=0..3.5 (includes windows)',cases=records)
(ROOT/'results/ignition-boundary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
