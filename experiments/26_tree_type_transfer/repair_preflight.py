"""Prepare corrected candidates without modifying frozen inputs or submitting jobs."""
import re,json,hashlib,subprocess,os
from pathlib import Path
from preflight import BINARY
R=Path(__file__).parent
rows=[]
for c in json.loads((R/'cases.json').read_text()):
 original=(R/'decks'/(c['case']+'.fds')).read_text()
 ramps={}
 for b in re.findall(r'&RAMP\b.*?/',original,re.S):
  name=re.search(r"ID='([^']+)'",b)[1];t=float(re.search(r'\bT\s*=\s*([-+.\deE]+)',b)[1]);ramps.setdefault(name,[]).append(t)
 bad=[k for k,ts in ramps.items() if any(b<=a for a,b in zip(ts,ts[1:]))]
 row={'case':c['case'],'invalid_ramps':bad}
 if bad:
  assert c['family']=='single' and bad==['source']
  # Only unused legacy SURF and its ramp are removed; active contact ramp is byte-identical.
  assert len(re.findall(r"'IGNITOR'",original))==1
  fixed=re.sub(r"&SURF ID='IGNITOR'.*?/\n",'',original,flags=re.S)
  fixed=re.sub(r"&RAMP ID='source'.*?/\n",'',fixed,flags=re.S)
  assert re.findall(r'&INIT\b.*?/',fixed,re.S)==re.findall(r'&INIT\b.*?/',original,re.S)
  folder=R/'data/repair-preflight'/c['case'];folder.mkdir(parents=True,exist_ok=True)
  (folder/'candidate.fds').write_text(fixed)
  short=fixed.replace('T_END=180','T_END=.1')
  (folder/'check.fds').write_text(short)
  with (folder/'initial.log').open('w') as log:
   p=subprocess.run([str(BINARY),'check.fds'],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE'),stdout=log,stderr=subprocess.STDOUT,timeout=240)
  row.update(candidate_sha256=hashlib.sha256(fixed.encode()).hexdigest(),native_passed=p.returncode==0 and 'completed successfully' in (folder/'initial.log').read_text().lower(),frozen_particles_unchanged=True)
  assert row['native_passed'],row
 rows.append(row)
 (R/'results/repair-preflight.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(c['case'],bad,flush=True)
