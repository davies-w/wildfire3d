import json,os,subprocess,hashlib,csv,tarfile,traceback,time
from pathlib import Path
import runner
ROOT=Path('/study');cases=json.loads((ROOT/'cases.json').read_text());group=json.loads((ROOT/'group.json').read_text())
Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
start=time.monotonic()
try:
 for c in cases:
  name=c['case'];source=(ROOT/'decks'/f'{name}.fds').read_text();assert hashlib.sha256(source.encode()).hexdigest()==c['deck_sha256']
  folder=ROOT/'preflight'/name;folder.mkdir(parents=True)
  s=source.replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01')
  env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
  for stage,deck in [('initial',s),('resumed',s.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'))]:
   (folder/'check.fds').write_text(deck)
   with (folder/(stage+'.log')).open('w') as f:p=subprocess.run([runner.BINARY,'check.fds'],cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150)
   assert p.returncode==0 and 'completed successfully' in (folder/(stage+'.log')).read_text().lower()
   assert list(folder.glob('*.restart'))
  with (folder/(name+'_devc.csv')).open() as f:rows=list(csv.reader(f));assert float(rows[-1][0])>=.15-1e-6
  out=ROOT/'data'/name;out.mkdir(parents=True);(out/'linux-resume-preflight.json').write_text(json.dumps(dict(passed=True,binary_sha256=hashlib.sha256(Path(runner.BINARY).read_bytes()).hexdigest())))
  remaining=group['duration_s']-720-(time.monotonic()-start)
  assert remaining>60,'Insufficient remaining reserved lifetime'
  result=runner.run(c,min(c['solve_limit_s'],remaining))
except Exception:
 traceback.print_exc()
 archive=Path('/tmp')/'worker-failure.tar.gz'
 with tarfile.open(archive,'w:gz') as t:
  if (ROOT/'preflight').exists():t.add(ROOT/'preflight',arcname='preflight')
  if (ROOT/'data').exists():t.add(ROOT/'data',arcname='data')
 runner.upload(archive,'worker-failure.tar.gz')
 raise
