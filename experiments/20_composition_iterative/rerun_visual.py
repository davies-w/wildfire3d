"""Repeat frozen scene locally, changing only output settings; no ember physics added."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from scene import write,ROOT
CASE='confirm20_ACG_3200_s4321'
r=next(r for r in json.loads((ROOT/'confirmation-inputs.json').read_text()) if r['case']==CASE)
write(r)
s=(ROOT/'decks'/f'{CASE}.fds').read_text()
original=json.loads((ROOT/'batches/confirmation20/data/cloud'/CASE/'result.json').read_text())
assert hashlib.sha256(s.encode()).hexdigest()==original['deck_sha256']
s=s.replace('SMOKE3D=F','SMOKE3D=T, DT_SMOKE3D=.5').replace('DT_PART=30.','DT_PART=.5').replace('SAMPLING_FACTOR=10','SAMPLING_FACTOR=1')
folder=ROOT/'data/full_visual';folder.mkdir(exist_ok=True)
(folder/f'{CASE}.fds').write_text(s)
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
start=time.time()
with (folder/'run.log').open('w') as log:
 result=subprocess.run([str(binary),f'{CASE}.fds'],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=log,stderr=subprocess.STDOUT,timeout=1800)
report=dict(returncode=result.returncode,wall_seconds=time.time()-start,source_deck_sha256=original['deck_sha256'],visual_deck_sha256=hashlib.sha256(s.encode()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cloud_spend_usd=0,embers=False)
(folder/'provenance.json').write_text(json.dumps(report,indent=2))
assert result.returncode==0 and 'completed successfully' in (folder/'run.log').read_text().lower()
print(json.dumps(report))
