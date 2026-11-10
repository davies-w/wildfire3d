"""Match the retained transfer sample to its pinned cloud inventory and backup receipt."""
import base64,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07';sample=p/'raw-migration-sample.part'
with sample.open('rb') as f:md=base64.b64encode(hashlib.file_digest(f,'md5').digest()).decode()
items=[x for x in json.loads((p/'raw-migration-inventory.json').read_text()) if x.get('md5Hash')==md];assert len(items)==1
item=items[0];assert int(item['size'])==sample.stat().st_size
manifest=str(Path(item['name']).parent/'archive-manifest.json');proofs=[]
for f in (p/'raw-migration-receipts').glob('*.json'):
 r=json.loads(f.read_text())
 if r['source_manifest']==manifest:
  assert r['passed'] and r['verification']['remote_size_and_xet_verified'];proofs.append(str(f.relative_to(ROOT)))
assert proofs
(p/'raw-migration-sample-reconciliation.json').write_text(json.dumps({'passed':True,'sample_md5_base64':md,'source_object':item['name'],'source_generation':item['generation'],'archive_receipts':proofs,'sample_retained':True},indent=2)+'\n');print('Sample matched pinned part and verified archive receipt')
