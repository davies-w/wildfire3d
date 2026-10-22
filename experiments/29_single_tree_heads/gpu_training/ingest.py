"""Verify and adopt completed cloud outputs; never runs training."""
from pathlib import Path
import json,hashlib,tarfile,shutil
R=Path(__file__).parent;P=R.parent;D=R/'data/train01'
finished=json.loads((D/'complete.json').read_text());assert finished['success'];assert not any(json.loads((R/'results/cleanup.json').read_text()).values())
h=hashlib.sha256()
with (D/'outputs.tar').open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
assert h.hexdigest()==finished['output_sha256']
stage=R/'data/adopted';stage.mkdir(exist_ok=True)
with tarfile.open(D/'outputs.tar') as t:
 for m in t.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
 t.extractall(stage)
files=[stage/'data/models/heads.pt',stage/'results/heads-training.json',*list((stage/'results').glob('*-evaluation.json')),*list((stage/'data/validation_predictions').glob('*.npy'))]
old=R/'data/prior-local-results';old.mkdir(exist_ok=True);adopted={}
for src in files:
 rel=src.relative_to(stage);dst=P/rel
 if dst.exists() and dst.read_bytes()!=src.read_bytes():
  backup=old/rel;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,backup)
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);adopted[str(rel)]=hashlib.sha256(src.read_bytes()).hexdigest()
(R/'results/adopted.json').write_text(json.dumps(adopted,indent=2));print('Adopted',len(files),'verified outputs')
