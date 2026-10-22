"""Push DVC data ONLY to configured local mirror; never contact public archive."""
import json,subprocess,time,fcntl
from pathlib import Path
import yaml
R=Path(__file__).resolve().parents[1];V=R/'.venv/bin';E=R/'experiments/33_representation_loss'
with (E/'data/local-archive.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 subprocess.run([str(V/'dvc'),'commit','-f','experiments/32_tree_expansion/dvc.yaml:archive_cloud'],cwd=R,check=True)
 targets=[]
 for root in sorted((R/'experiments').iterdir()):
  if root.name[:2] not in ['27','28','29','30','31','32','33']:continue
  for p in root.rglob('dvc.lock'):
   if 'data' in p.relative_to(root).parts:continue
   doc=yaml.safe_load(p.read_text()) or {}
   for stage,spec in doc.get('stages',{}).items():
    if any(o.get('md5') for o in spec.get('outs',[])):targets.append(str(p.with_name('dvc.yaml').relative_to(R))+':'+stage)
 failures=[]
 for target in targets:
  p=subprocess.run([str(V/'dvc'),'push','-r','mirror',target],cwd=R,text=True,capture_output=True)
  if p.returncode:failures.append(dict(target=target,error=p.stderr[-3000:]))
  (E/'results/local-archive-progress.json').write_text(json.dumps(dict(total=len(targets),current=target,failures=failures),indent=2))
 (E/'results/local-archive-complete.json').write_text(json.dumps(dict(finished_unix=time.time(),targets=targets,failures=failures,scope='LOCAL mirror only; public upload awaits approval'),indent=2))
