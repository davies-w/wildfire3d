"""Account for reviewed experiment inventory and list every remaining audit item."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07'
reviews=['historical-array-policy-review.json','historical-support-policy-review.json','historical-geometry-policy-review.json','historical-text-policy-review.json','historical-archive-policy-review.json','historical-render-source-review.json']
accounted={}
for name in reviews:
 r=json.loads((p/name).read_text())
 for x in r['files']:accounted[x['path']]={'review':name,'md5':x['md5']}
 for x in r['excluded']:accounted[x['path']]={'review':name,'excluded':x['reason']}
hashes=set()
for f in (p/'missing-output-remote').glob('*.dir'):
 assert hashlib.md5(f.read_bytes()).hexdigest()==f.name[:-4]
 hashes.update(x['md5'] for x in json.loads(f.read_text()))
r=json.loads((p/'historical-render-source-review.json').read_text())
for x in r['files']:
 with (ROOT/x['path']).open('rb') as f:assert hashlib.file_digest(f,'md5').hexdigest()==x['md5']
 assert x['md5'] in hashes
rows=list(csv.DictReader((ROOT/'experiments/43_repository_preservation/results/file-tracking-audit/not-tracked-experiment-files.csv').open()))
remaining=[]
for x in rows:
 if x['path'] not in accounted:
  f=ROOT/x['path'];d=dict(x)
  if f.is_file():
   with f.open('rb') as h:d['current_md5']=hashlib.file_digest(h,'md5').hexdigest()
   d['existing_remote_manifest_match']=d['current_md5'] in hashes
  remaining.append(d)
result={'inventory_rows':len(rows),'reviewed_rows':sum(x['path'] in accounted for x in rows),'render_source_exact_remote_matches':len(r['files']),'remaining':remaining,'remaining_without_remote_match':[x for x in remaining if not x.get('existing_remote_manifest_match')],'scope':'Original experiment audit inventory only; private operational inventory and external working folders require separate classification. Remote manifest matches establish object availability, not fresh full restoration.'}
(p/'remaining-audit-inventory.json').write_text(json.dumps(result,indent=2)+'\n');print('Reviewed',result['reviewed_rows'],'of',len(rows),'remaining',len(remaining),'without remote hash match',len(result['remaining_without_remote_match']))
for x in result['remaining_without_remote_match']:print(x['path'])
