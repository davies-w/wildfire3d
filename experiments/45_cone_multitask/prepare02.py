"""New uniquely named pool after audited pre-ownership failure; identical science."""
from pathlib import Path
import json,shutil,os,hashlib
R=Path(__file__).resolve().parent;D=R/'data/training02';O=R/'results02';O.mkdir(exist_ok=True)
assert json.loads((R/'results/pool-closed.json').read_text())['passed'];assert json.loads((R/'results/failure-audit.json').read_text())['no_completed_epochs'];assert not (O/'submission-intent.json').exists();assert not D.exists()
D.mkdir();p=json.loads((R/'results/package.json').read_text());same={}
for name,sha in p['files'].items():
 src=R/'data/training'/name;assert hashlib.sha256(src.read_bytes()).hexdigest()==sha;dst=D/name;dst.parent.mkdir(parents=True,exist_ok=True)
 if src.suffix=='.npz':os.link(src,dst)
 else:shutil.copy2(src,dst)
 same[name]=sha
(O/'science-equivalence.json').write_text(json.dumps(dict(passed=True,files=same,fresh_weights=True,no_prior_epochs=True,change='Only controller idempotent HTTP retries and unique runtime prefix; scientific code/labels/optimizer unchanged'),indent=2)+'\n')
print('Prepared identical scientific inputs for new pool02')
