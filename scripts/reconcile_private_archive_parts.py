"""Reconcile retained archive parts by SHA256 without publishing private records."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07'
queue=json.loads((p/'all-local-raw-archive-queue.json').read_text())['archives'];proofs={}
for f in (p/'local-archive-preservation').glob('*/complete.json'):
 r=json.loads(f.read_text());assert r['passed'] and r['restoration_sha256_verified'];proofs[r['source_manifest']]=str(f.relative_to(ROOT))
known={}
for a in queue:
 assert a['manifest'] in proofs
 for part in a['parts']:known.setdefault(part['sha256'],[]).append(proofs[a['manifest']])
rows=[]
for x in csv.DictReader((ROOT/'experiments/43_repository_preservation/results/file-tracking-audit/not-tracked-project-files.csv').open()):
 if Path(x['path']).suffix!='.part':continue
 f=ROOT/x['path'];assert f.is_file() and not f.is_symlink()
 with f.open('rb') as h:sha=hashlib.file_digest(h,'sha256').hexdigest()
 rows.append({'path':x['path'],'sha256':sha,'verified_archive_receipts':known.get(sha,[])})
result={'parts':rows,'covered':sum(bool(x['verified_archive_receipts']) for x in rows),'unmatched':[x for x in rows if not x['verified_archive_receipts']]}
(p/'private-archive-part-reconciliation.json').write_text(json.dumps(result,indent=2)+'\n');print('Covered',result['covered'],'of',len(rows));print('Unmatched',len(result['unmatched']))
