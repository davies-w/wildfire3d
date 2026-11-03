"""Regression proof from preserved cloud outputs; no solver execution."""
from pathlib import Path
import json,io,tarfile,csv,hashlib
from pilot_worker04 import mass_row
R=Path(__file__).resolve().parent;D=R/'data/startup03';D.mkdir(exist_ok=True);proofs=[]
for p in sorted((R/'private03/failed-pilot03/canary').glob('*/archive-manifest.json')):
 m=json.loads(p.read_text());parts=[]
 for v in m['parts']:
  b=(p.parent/v['name']).read_bytes();assert hashlib.sha256(b).hexdigest()==v['sha256'];parts.append(b)
 t=tarfile.open(fileobj=io.BytesIO(b''.join(parts)),mode='r:gz');config=json.load(t.extractfile('evidence/input.json'));c=config['case']
 member=next(v for v in t.getnames() if v.endswith('_devc.csv'));data=t.extractfile(member).read();rows=list(csv.reader(io.StringIO(data.decode())));rows=[dict(zip(rows[1],map(float,v))) for v in rows[2:]]
 assert rows[0]['Time']==0 and all(rows[0][k+' mass']==0 for k in c['expected_wet_mass_kg'])
 first=mass_row(rows)
 errors={k:abs(first[k+' mass']-v)/v for k,v in c['expected_wet_mass_kg'].items()};assert max(errors.values())<.01
 (D/(c['pilot_case']+'.csv')).write_bytes(data);proofs.append(dict(case=c['pilot_case'],time=first['Time'],relative_errors=errors,csv_sha256=hashlib.sha256(data).hexdigest()))
assert len(proofs)==4
(D/'proof.json').write_text(json.dumps(dict(passed=True,cases=proofs,scope='Mass accounting at first positive simulation time from four actual cloud FDS probes; initial time-zero row precedes particle initialization. Restart and full solves not yet tested.'),indent=2)+'\n')
print('Four actual cloud mass checks pass; maximum relative error',max(e for p in proofs for e in p['relative_errors'].values()))
