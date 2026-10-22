import csv,json,os,subprocess,math
from pathlib import Path
from scene import ROOT,deck,cases
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
results=[]
for c in cases():
 w=ROOT/'data/preflight'/c['case'];w.mkdir(parents=True,exist_ok=True);s,r=deck(c,horizon=1.05);(w/'check.fds').write_text(s)
 with (w/'run.log').open('w') as f:p=subprocess.run([str(binary),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=180)
 text=(w/'run.log').read_text();assert p.returncode==0 and 'completed successfully' in text.lower(),text[-4000:]
 with (w/(c['case']+'_devc.csv')).open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('\"') for k in next(it)];rows=[dict(zip(keys,map(float,row))) for row in it if row]
 assert len(rows)>=2 and all(math.isfinite(v) for row in rows for v in row.values())
 expected=r['nominal_dry_fuel_kg']*1.14;actual=sum(v for k,v in rows[1].items() if k.startswith('mass '))
 assert (expected==0 and actual==0) or abs(actual-expected)/expected<.15,(actual,expected)
 results.append(dict(case=c['case'],passed=True,nominal_wet_mass_kg=expected,initialized_wet_mass_kg=actual,device_rows=len(rows)))
(ROOT/'results/preflight.json').write_text(json.dumps(results,indent=2));print(results)
