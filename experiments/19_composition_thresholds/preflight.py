"""Local startup checks for the added layout and maximum source power."""
import csv,json,math,os,subprocess
from generate import ROOT,write
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
results=[]
for layout in ('A','AD','ABC'):
    c=write('preflight_'+layout,layout,3200,horizon=1.05,split='preflight')
    folder=ROOT/'data/preflight'/c['case'];folder.mkdir(parents=True,exist_ok=True)
    with (folder/'run.log').open('w') as log:
        r=subprocess.run([str(binary),str(ROOT/'decks'/(c['case']+'.fds'))],cwd=folder,
            env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),
            stdout=log,stderr=subprocess.STDOUT,timeout=120)
    text=(folder/'run.log').read_text()
    assert r.returncode==0 and 'completed successfully' in text.lower(),text[-4000:]
    with (folder/(c['case']+'_devc.csv')).open() as f:
        it=csv.reader(f);next(it);keys=[x.strip().strip('"') for x in next(it)]
        rows=[list(map(float,row)) for row in it if row]
    assert all(math.isfinite(v) and v>-1e10 for row in rows for v in row)
    assert all(rows[-1][i]>0 for i,k in enumerate(keys) if k.startswith('mass '))
    for p in folder.glob('*.restart'):p.unlink()
    results.append(dict(case=c['case'],completed=True))
(ROOT/'results/local-preflight.json').write_text(json.dumps(results,indent=2)+'\n')
checks=json.loads((ROOT/'results/acquisition-check.json').read_text())
assert all(r['passed'] for r in checks)
(ROOT/'results/design-check.json').write_text(json.dumps(dict(passed=True,max_new_runs=37))+'\n')
print('Local high-power startup, new layout, face sensors and fuel-mass checks passed.')
