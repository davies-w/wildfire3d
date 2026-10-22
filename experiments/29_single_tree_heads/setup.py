import json,hashlib,os,shutil
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'28_single_tree_repair'
for d in ['data/fields','data/models','data/validation_predictions','results','results/visuals']:(R/d).mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((P/'results/prediction-freeze.json').read_text());assert all(sha(P/p)==h for p,h in f['files'].items())
cs=[c for c in json.loads((P/'cases.json').read_text()) if c['split'] in ['train','validation']];sources={}
for c in cs:
 for suffix in ['.npy','-time.npy','.json']:
  src=P/'data/fields'/(c['case']+suffix);dst=R/'data/fields'/src.name
  if not dst.exists():os.link(src,dst)
  sources[str(src)]=sha(src)
shutil.copy2(P/'data/models/physical.pt',R/'data/models/previous.pt')
(R/'cases.json').write_text(json.dumps(cs,indent=2));(R/'results/reuse.json').write_text(json.dumps(dict(sources=sources,parent_freeze_sha256=sha(P/'results/prediction-freeze.json'),parent_weights_sha256=sha(R/'data/models/previous.pt'),rule='32 train and6 validation only; both prior test sets excluded; no paid jobs'),indent=2))
print('Prepared development-only dataset',flush=True)
