import json,hashlib,shutil,os
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'27_single_tree_cnn'
for d in ['data/fields','data/models','data/predictions','results']:(R/d).mkdir(parents=True,exist_ok=True)
f=json.loads((P/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((P/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
cases=[c for c in json.loads((P/'cases.json').read_text()) if c['split'] in ['train','validation']]
sources={}
for c in cases:
 for suffix in ['.npy','-time.npy','.json']:
  src=P/'data/fields'/(c['case']+suffix);dst=R/'data/fields'/src.name
  if not dst.exists():os.link(src,dst)
  sources[str(src)]=hashlib.sha256(src.read_bytes()).hexdigest()
shutil.copy2(P/'data/models/cnn_32.pt',R/'data/models/original.pt')
(R/'cases.json').write_text(json.dumps(cases,indent=2))
(R/'results/reused-data.json').write_text(json.dumps(dict(sources=sources,parent_freeze_sha256=hashlib.sha256((P/'results/prediction-freeze.json').read_bytes()).hexdigest(),rule='Immutable development fields only. No prior test fields linked.'),indent=2))
print('Reused32 training+6 validation; parent freeze verified',flush=True)
