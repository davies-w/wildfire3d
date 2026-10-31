"""Preserve verified scientific progress separately from private budget evidence."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
R=Path(__file__).resolve().parent;D=R/'data/progress-public';D.mkdir(exist_ok=True)
for candidate in ['or','ia','sc']:
 proof=R/'results03'/('progress-'+candidate+'-verified.json')
 if not proof.exists():continue
 entries=json.loads(proof.read_text())['scores']
 for name,entry in entries.items():
  f=R/('data/progress'+candidate)/name;b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==entry['sha256']
  dst=D/'epochs'/name;dst.parent.mkdir(exist_ok=True)
  if dst.exists():assert dst.read_bytes()==b,'Conflicting branch epochs'
  else:dst.write_bytes(b)
 audit=R/'results03'/('startup-audit-'+candidate+'.json')
 if audit.exists():
  a=json.loads(audit.read_text());assert a['passed']
  (D/('startup-'+candidate+'.json')).write_text(json.dumps({k:v['value'] for k,v in a['proofs'].items()},indent=2)+'\n')
subprocess.run([sys.executable,str(R/'plot_learning_curve.py'),'--output',str(D/'learning-curve.png')],check=True)
manifest={str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file() and f.name!='manifest.json'}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
