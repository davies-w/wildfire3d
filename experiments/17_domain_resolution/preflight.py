"""Local syntax, mesh connectivity and particle initialization checks only."""
import os,subprocess,json
from pathlib import Path
from generate import ROOT,DOMAINS,write
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
results=[]
for mode in DOMAINS:
    c=write('preflight_'+mode,mode,1000,.05);name=c['case'];d=ROOT/'data/preflight'/name;d.mkdir(parents=True,exist_ok=True)
    with (d/'run.log').open('w') as f:
        p=subprocess.run([str(binary),str(ROOT/'decks'/f'{name}.fds')],cwd=d,env=dict(os.environ,OMP_NUM_THREADS='4'),stdout=f,stderr=subprocess.STDOUT,timeout=90)
    log=(d/'run.log').read_text();ok=p.returncode==0 and 'completed successfully' in log.lower()
    results.append(dict(c,returncode=p.returncode,completed=ok))
    if not ok:print(log[-7000:]);raise RuntimeError(name)
(ROOT/'results/local-preflight.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
