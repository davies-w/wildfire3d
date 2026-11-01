"""Adopt the audited snapshot without rerunning any experiment."""
from pathlib import Path
import os,shutil,subprocess
R=Path(__file__).resolve().parent;ROOT=R.parents[1];ISO=Path('/tmp/gru-export-dvc.zcBQ9K');rel=R.relative_to(ROOT);dest=ISO/rel
assert (R/'results/snapshot-complete.json').exists()
assert (R/'results/privacy-reviewed.json').exists()
dest.mkdir(parents=True,exist_ok=True)
for name in ['audit.py','finalize.py','dvc.yaml']:shutil.copy2(R/name,dest/name)
shutil.copytree(R/'data/public',dest/'data/public',copy_function=os.link,dirs_exist_ok=False)
for args in [['commit','-f',str(rel/'dvc.yaml')+':snapshot'],['push','-r','mirror',str(rel/'dvc.yaml')+':snapshot']]:
 subprocess.run([str(ROOT/'.venv/bin/dvc'),*args],cwd=ISO,check=True)
shutil.copy2(dest/'dvc.lock',R/'dvc.lock')
