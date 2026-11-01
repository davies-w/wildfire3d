"""Adopt reviewed outputs without rerunning any experiment; push local mirror."""
from pathlib import Path
import os,shutil,subprocess,argparse
R=Path(__file__).resolve().parent;ROOT=R.parents[1];ISO=Path('/tmp/gru-export-dvc.zcBQ9K');rel=R.relative_to(ROOT);dest=ISO/rel
parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['snapshot','private'],default='snapshot');args=parser.parse_args()
assert (R/'results/snapshot-complete.json').exists()
assert (R/'results/privacy-reviewed.json').exists()
out='data/public' if args.stage=='snapshot' else 'data/private';assert (R/out).is_dir()
dest.mkdir(parents=True,exist_ok=True)
for name in ['audit.py','finalize.py','repair_metadata.py','preserve_private.py','dvc.yaml']:shutil.copy2(R/name,dest/name)
# Only replace this isolated staging output; originals and shared cache remain.
if (dest/out).exists():shutil.rmtree(dest/out)
shutil.copytree(R/out,dest/out,copy_function=os.link)
for command in [['commit','-f',str(rel/'dvc.yaml')+':'+args.stage],['push','-r','mirror',str(rel/'dvc.yaml')+':'+args.stage]]:
 subprocess.run([str(ROOT/'.venv/bin/dvc'),*command],cwd=ISO,check=True)
shutil.copy2(dest/'dvc.lock',R/'dvc.lock')
