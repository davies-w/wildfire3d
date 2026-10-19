"""Native 4.1-second solve verifies actual volume frame cadence before paid development."""
import subprocess,os,json
from pathlib import Path
from fields import read_slice
R=Path(__file__).parent;c=json.loads((R/'cases.json').read_text())[6];p=R/'data/cadence-preflight';p.mkdir(exist_ok=True)
s=(R/'decks'/(c['case']+'.fds')).read_text().replace('T_END=180','T_END=4.1');(p/'check.fds').write_text(s)
with (p/'run.log').open('w') as f:r=subprocess.run([str(R.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'),'check.fds'],cwd=p,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert r.returncode==0
rows=[]
for f in p.glob('*.sf'):
 name,unit,b,t,a=read_slice(f);assert len(t)>=3 and 1.9<t[1]<2.2 and t[-1]>=4, (name,t);rows.append(dict(quantity=name,times=t.tolist(),units=unit))
assert len(rows)==6
(R/'results/cadence-preflight.json').write_text(json.dumps(dict(passed=True,fields=rows),indent=2));print('Actual 3D output cadence verified')
