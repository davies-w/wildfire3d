import csv,hashlib,json,os,subprocess
from pathlib import Path
import runner
import traceback,tarfile
try:
 root=Path('/study');c=json.loads((root/'case.json').read_text());name=c['case'];w=root/'linux_resume';w.mkdir();s=(root/'decks'/f'{name}.fds').read_text().replace('T_END=90','T_END=.1').replace('DT_RESTART=10.','DT_RESTART=.05').replace('DT_DEVC=.5','DT_DEVC=.01')
 env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
 def solve(s,label):
  (w/'check.fds').write_text(s)
  with (w/(label+'.log')).open('w') as f:p=subprocess.run([runner.BINARY,str(w/'check.fds')],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
  assert p.returncode==0 and 'completed successfully' in (w/(label+'.log')).read_text().lower()
 solve(s,'initial');checkpoints=list(w.glob('*.restart'));assert checkpoints
 checkpoint_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in checkpoints}
 solve(s.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'),'resumed')
 with (w/(name+'_devc.csv')).open() as f:
  rows=list(csv.reader(f));last=float(rows[-1][0]);assert last>=.15-1e-6
 folder=root/'data'/name;folder.mkdir(parents=True);(folder/'linux-resume-preflight.json').write_text(json.dumps(dict(passed=True,last_time=last,initial_checkpoint_hashes=checkpoint_hashes,binary_sha256=hashlib.sha256(Path(runner.BINARY).read_bytes()).hexdigest())))
 Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
 runner.run(c,5400)
except Exception:
 traceback.print_exc()
 failure=Path('/tmp')/('b21_combined_0'+'-worker-failure.tar.gz')
 with tarfile.open(failure,'w:gz') as archive:archive.add(Path('/study/linux_resume'),arcname='linux_resume')
 runner.upload(failure,failure.name)
 raise SystemExit(1)
