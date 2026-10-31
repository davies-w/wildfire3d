"""Adopt current outputs in isolated DVC checkout; push mirror, copy lock back. Public sync is separate."""
from pathlib import Path
import shutil,subprocess,yaml
r=Path(__file__).resolve().parent;root=r.parents[1];iso=Path('/tmp/gru-export-dvc.zcBQ9K');rel=r.relative_to(root);d=iso/rel;d.mkdir(parents=True,exist_ok=True)
for p in r.iterdir():
 if p.is_file():shutil.copy2(p,d/p.name)
for out in ['training','progress-public','provenance','pool01-results','analysis','public','report-public']:
 if (r/'data'/out).exists():shutil.copytree(r/'data'/out,d/'data'/out,dirs_exist_ok=True)
for stage,out in [('prepare','training'),('progress','progress-public'),('preserve','provenance'),('collect','pool01-results'),('analysis','analysis'),('public','public'),('reports','report-public')]:
 if not (r/'data'/out).exists():continue
 if stage=='collect' and not (r/'results/collected.json').exists():continue
 if stage=='preserve' and not (r/'data/provenance').exists():continue
 subprocess.run([str(root/'.venv/bin/dvc'),'commit','-f',str(rel/'dvc.yaml')+':'+stage],cwd=iso,check=True)
 subprocess.run([str(root/'.venv/bin/dvc'),'push','-r','mirror',str(rel/'dvc.yaml')+':'+stage],cwd=iso,check=True)
shutil.copy2(d/'dvc.lock',r/'dvc.lock')
