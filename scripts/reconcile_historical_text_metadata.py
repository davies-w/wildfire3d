"""Match reviewed text metadata to verified remote manifests, without publishing it."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'experiments/51_three_tree_campaign/private07'
checks=json.loads((p/'missing-output-remote/verification.json').read_text());owners={}
for check in checks:
 if not check['md5'].endswith('.dir'):continue
 assert check['download_md5_verified'] and check['all_member_paths_present']
 f=p/'missing-output-remote'/check['md5'];assert hashlib.md5(f.read_bytes()).hexdigest()==check['md5'][:-4]
 for x in json.loads(f.read_text()):owners.setdefault(x['md5'],[]).append(check['md5'])
r=json.loads((p/'historical-text-policy-review.json').read_text());rows=[]
for x in r['files']:
 f=ROOT/x['path']
 if f.name.startswith('ig_') and f.suffix=='.txt':continue
 with f.open('rb') as h:assert hashlib.file_digest(h,'md5').hexdigest()==x['md5']
 match=owners.get(x['md5'],[])
 if not match:assert x['path'].startswith('experiments/43_repository_preservation/results/'),x['path']
 rows.append({'path':x['path'],'md5':x['md5'],'remote_manifest_matches':match,'classification':'existing_remote_hash' if match else 'private_preservation_audit_metadata_retained'})
report={'records':rows,'remote_manifest_covered':sum(bool(x['remote_manifest_matches']) for x in rows),'private_audit_records':sum(not x['remote_manifest_matches'] for x in rows),'policy_exclusions':r['excluded'],'scope':'Current local hashes matched against verified old export manifests and remote member availability; no new metadata uploads and no full export restoration'}
(p/'historical-text-reconciliation.json').write_text(json.dumps(report,indent=2)+'\n');print(report['remote_manifest_covered'],'covered;',report['private_audit_records'],'private audit records;',len(report['policy_exclusions']),'policy exclusions')
