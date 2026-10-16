"""Very short local input checks; not a performance benchmark."""
import subprocess,os,re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
binary=Path(os.environ.get('FDS_BINARY') or str(ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'))
results=[]
for name in ['lot_a','hot_profile','hot_coarse','hot_radiation']:
 d=ROOT/'data/preflight'/name;d.mkdir(parents=True,exist_ok=True)
 deck=d/(name+'.fds');deck.write_text(re.sub(r'T_END=[\d.]+','T_END=0.01',(ROOT/'decks'/(name+'.fds')).read_text()))
 with (d/'run.log').open('w') as log:p=subprocess.run([str(binary),str(deck)],cwd=d,env=dict(os.environ,OMP_NUM_THREADS='4'),stdout=log,stderr=subprocess.STDOUT,timeout=60)
 text=(d/'run.log').read_text();results.append({'case':name,'returncode':p.returncode,'completed':'completed successfully' in text.lower()})
 if p.returncode:raise RuntimeError('Preflight failed: '+name)
(ROOT/'results/local-preflight.json').write_text(json.dumps(results,indent=2)+'\n')
