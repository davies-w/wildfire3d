"""Adopt reviewed output in temporary in-repo DVC checkout; no local mirror."""
from pathlib import Path
import os,shutil,subprocess,argparse,tempfile
R=Path(__file__).resolve().parent;ROOT=R.parents[1];rel=R.relative_to(ROOT)
parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['snapshot','private'],default='snapshot');args=parser.parse_args()
assert (R/'results/snapshot-complete.json').exists() and (R/'results/privacy-reviewed.json').exists()
out='data/public' if args.stage=='snapshot' else 'data/private';assert (R/out).is_dir()
base=ROOT/'.artifact-staging';base.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='dvc-track-',dir=base) as name:
 iso=Path(name);dest=iso/rel;dest.mkdir(parents=True)
 def dvc(*a):subprocess.run([str(ROOT/'.venv/bin/dvc'),*a],cwd=iso,check=True)
 dvc('init','--no-scm','--quiet');dvc('config','cache.dir',str(ROOT/'.dvc/cache'))
 for n in ['audit.py','finalize.py','repair_metadata.py','preserve_private.py','dvc.yaml','dvc.lock']:
  if (R/n).exists():shutil.copy2(R/n,dest/n)
 shutil.copytree(R/out,dest/out,copy_function=os.link)
 dvc('commit','-f',str(rel/'dvc.yaml')+':'+args.stage)
 shutil.copy2(dest/'dvc.lock',R/'dvc.lock')
print('Tracked',args.stage,'in cache. Public upload is separate; private data stays local.')
