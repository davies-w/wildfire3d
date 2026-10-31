"""Adopt existing outputs in isolated DVC checkout; scoped mirror push then copy lock."""
from pathlib import Path
import shutil,subprocess,yaml
r=Path(__file__).resolve().parent;root=r.parents[1];iso=Path('/tmp/gru-export-dvc.zcBQ9K');rel=r.relative_to(root);d=iso/rel;d.mkdir(parents=True,exist_ok=True)
for p in r.iterdir():
 if p.is_file():shutil.copy2(p,d/p.name)
stages=yaml.safe_load((r/'dvc.yaml').read_text())['stages']
for stage,definition in stages.items():
 out=next(iter(definition['outs'][0]));src=r/out
 if not src.exists():continue
 if stage=='collect' and not (r/'results02/collected.json').exists():continue
 shutil.copytree(src,d/out,dirs_exist_ok=True)
 subprocess.run([str(root/'.venv/bin/dvc'),'commit','-f',str(rel/'dvc.yaml')+':'+stage],cwd=iso,check=True)
 subprocess.run([str(root/'.venv/bin/dvc'),'push','-r','mirror',str(rel/'dvc.yaml')+':'+stage],cwd=iso,check=True)
shutil.copy2(d/'dvc.lock',r/'dvc.lock')
