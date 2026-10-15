"""Read raw cloud wall boundary output independently with native fds2ascii."""
import json,os,subprocess
from pathlib import Path
from study import ROOT,save
name='fire_medium';folder=ROOT/'data/cloud'/f'{name}_r1'
binary=Path(os.environ.get('FDS2ASCII') or str(ROOT.parents[1]/'FDS/install/bin/fds2ascii'))
dest=ROOT/'data/cloud_boundary';dest.mkdir(parents=True,exist_ok=True)
out=dest/'fire_medium_west_temperature.csv'
answers=f'{name}\n3\n1\nn\n7.0 8.0\n-1\n1\n1\n{out}\n'
p=subprocess.run([str(binary)],input=answers,text=True,cwd=folder,capture_output=True,timeout=60,check=True)
(dest/'fds2ascii.log').write_text(p.stdout+p.stderr)
values=[]
for line in out.read_text().splitlines():
    try:
        row=list(map(float,line.split(',')))
        if len(row)==4 and abs(row[0]-4)<1e-5:values.append(row[3])
    except ValueError:pass
if not values:raise RuntimeError('No target west-face samples')
save(ROOT/'results/cloud-boundary.json',dict(case=name,surface='TARGET west face x=4 m',quantity='WALL TEMPERATURE',averaging_window_s=[7,8],min_C=min(values),max_C=max(values),samples=len(values)))
print(min(values),max(values))
