"""Classify original audit candidates using preservation receipts and explicit exclusions."""
import csv,json,collections,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07';audit=ROOT/'experiments/43_repository_preservation/results/file-tracking-audit'
covered={}
for f in p.glob('*/source-map.json'):
 proof=f.with_name('complete.json')
 if not proof.exists():continue
 r=json.loads(proof.read_text())
 if not r.get('passed'):continue
 rows=json.loads(f.read_text())
 if not isinstance(rows,list):continue
 for x in rows:
  if 'original_path' in x:covered[x['original_path']]=str(proof.relative_to(ROOT))
private_parts=json.loads((p/'private-archive-part-reconciliation.json').read_text())['parts'];partpaths={x['path'] for x in private_parts}
assert json.loads((p/'unmanifested-archive-preservation/complete.json').read_text())['passed']
assert json.loads((p/'raw-migration-sample-reconciliation.json').read_text())['passed']
remote={x['path'] for x in json.loads((p/'historical-text-reconciliation.json').read_text())['records'] if x['remote_manifest_matches']}
remote.update(x['path'] for x in json.loads((p/'remaining-audit-inventory.json').read_text())['remaining'] if x.get('existing_remote_manifest_match'))
remote.update(x['path'] for x in json.loads((p/'historical-render-source-review.json').read_text())['files'])
excluded={}
for f in p.glob('*review.json'):
 try:r=json.loads(f.read_text())
 except ValueError:continue
 if not isinstance(r,dict) or not isinstance(r.get('excluded',[]),list):continue
 for x in r.get('excluded',[]):
  if isinstance(x,dict) and 'path' in x:excluded[x['path']]=x.get('reason',x.get('exclusion_reason','policy exclusion'))
git_paths=set(subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True).splitlines())
rows={x['path']:x for name in ['not-tracked-experiment-files.csv','not-tracked-project-files.csv'] for x in csv.DictReader((audit/name).open())};result=[]
for name,x in rows.items():
 f=Path(name);parts=f.parts;reason=None
 if name in git_paths:reason='git_tracked_metadata'
 elif name in covered:reason='preserved_scoped_batch'
 elif name in partpaths:reason='archive_part_reconciled'
 elif name in remote:reason='existing_remote_hash'
 elif name in excluded:reason='policy_excluded_retained'
 elif any(t in parts for t in ['.git','__pycache__']) or f.name=='.DS_Store' or f.suffix in {'.lock','.pid','.pyc'}:reason='tool_state_retained'
 elif '/results/direct-hf/' in name:reason='private_preservation_bookkeeping'
 elif any(t.startswith('billing-audit') for t in parts):reason='private_financial_retained'
 elif any(t.startswith('private') for t in parts) and f.suffix in {'.json','.xz','.txt','.bin','.dir'}:reason='private_operational_retained'
 elif name.startswith(('experiments/45_','experiments/46_')) and (f.suffix=='.json' or 'job-status.json.' in f.name or f.name=='upload-probe.bin'):reason='private_operational_retained'
 elif any(t.startswith('private') for t in parts) and (f.name.startswith(('job-status.','readiness-status.','controller-error.')) or f.suffix in {'.tgz','.stderr','.py','.jsonl'}):reason='private_operational_retained'
 elif name.startswith(('experiments/45_','experiments/46_')) and f.name.startswith('preflight-status.'):reason='private_operational_retained'
 elif name.startswith('experiments/43_repository_preservation/results/') and f.suffix=='.json':reason='private_preservation_bookkeeping'
 result.append({'path':name,'classification':reason or 'UNRESOLVED'})
counts=collections.Counter(x['classification'] for x in result);out={'scope':'Union of two original audit candidate CSVs, not every historical Git revision or external filesystem','counts':dict(counts),'records':result,'unresolved':[x for x in result if x['classification']=='UNRESOLVED']};(p/'final-inventory-classification.json').write_text(json.dumps(out,indent=2)+'\n');print(dict(counts));print([x['path'] for x in out['unresolved']][:30])
