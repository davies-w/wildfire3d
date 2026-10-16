"""Independent raw boundary check for the main structure's west face."""
import os,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
binary=Path(os.environ.get('FDS2ASCII') or str(ROOT.parents[1]/'FDS/install/bin/fds2ascii'))
dest=ROOT/'data/boundary';dest.mkdir(parents=True,exist_ok=True);results=[]
for folder in sorted((ROOT/'data/cloud').glob('*')):
 if not (folder/'result.json').exists() or folder.name=='smoke':continue
 d=json.loads((folder/'result.json').read_text())
 if not d['full_horizon'] or d['horizon_s']!=30:continue
 name=folder.name;out=dest/(name+'.csv')
 if not out.exists():
  answers=f'{name}\n3\n1\nn\n20.0 30.0\n-1\n1\n1\n{out}\n'
  p=subprocess.run([str(binary)],cwd=folder,input=answers,capture_output=True,text=True,timeout=60,check=True)
  (dest/(name+'.log')).write_text(p.stdout+p.stderr)
 values=[]
 for line in out.read_text().splitlines():
  try:
   row=list(map(float,line.split(',')))
   if len(row)==4 and abs(row[0]-18)<1e-5 and 8<=row[1]<=16 and 0<=row[2]<=3.5:values.append(row[3])
  except ValueError:pass
 if not values:raise RuntimeError('Missing house west-face data: '+name)
 results.append(dict(case=name,min_C=min(values),max_C=max(values),samples=len(values)))
(ROOT/'results/boundary.json').write_text(json.dumps({'surface':'Main structure west plane x=18, y=8..16,z=0..3.5; includes windows','quantity':'WALL TEMPERATURE','averaging_window_s':[20,30],'cases':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
