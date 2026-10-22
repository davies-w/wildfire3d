"""Local short initialization checks, never a cloud launch."""
import json,os,subprocess
from pathlib import Path
from scene import ROOT,write
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
cases=[dict(case='check_bare',layout='AC',vegetation='',total_source_kw=1700),
       dict(case='check_removed',layout='AD',vegetation='A',total_source_kw=1700),
       dict(case='check_new',layout='AF',total_source_kw=1700,duration_s=10)]
results=[]
for c in cases:
    r=write(c,horizon=1.05);folder=ROOT/'data/preflight'/r['case'];folder.mkdir(parents=True,exist_ok=True)
    with (folder/'run.log').open('w') as f:
        done=subprocess.run([str(binary),str(ROOT/'decks'/(r['case']+'.fds'))],cwd=folder,
            env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=120)
    text=(folder/'run.log').read_text();assert done.returncode==0 and 'completed successfully' in text.lower(),text[-4000:]
    for p in folder.glob('*.restart'):p.unlink()
    results.append(dict(case=r['case'],completed=True))
(ROOT/'results/preflight.json').write_text(json.dumps(results,indent=2)+'\n')
print('Bare-burner, crown-removal and new geometry/output startup checks passed.')
