from pathlib import Path
import os,subprocess,json
from generate import ROOT,DOMAINS,write
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
results=[]
for mode in DOMAINS:
    c=write('alignment_'+mode,mode,1000,0);d=ROOT/'data/alignment'/mode;d.mkdir(parents=True,exist_ok=True)
    p=subprocess.run([str(binary),str(ROOT/'decks'/(c['case']+'.fds'))],cwd=d,env=dict(os.environ,OMP_NUM_THREADS='4'),capture_output=True,text=True,timeout=90)
    (d/'run.log').write_text(p.stdout+p.stderr)
    ok=p.returncode==0 and 'ERROR' not in p.stdout+p.stderr
    results.append(dict(mode=mode,passed=ok,returncode=p.returncode))
    if not ok:print(p.stdout+p.stderr);raise RuntimeError(mode)
(ROOT/'results/alignment.json').write_text(json.dumps(results,indent=2)+'\n')
print(results)
