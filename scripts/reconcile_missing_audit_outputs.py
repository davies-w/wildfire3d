"""Reconcile old missing-output inventory without changing any data or DVC hash."""
from pathlib import Path
import json,hashlib,yaml
ROOT=Path(__file__).resolve().parents[1]
def main():
 private=ROOT/'experiments/51_three_tree_campaign/private07'
 rows=json.loads((ROOT/'experiments/43_repository_preservation/results/file-tracking-audit/summary.json').read_text())['missing_dvc_outputs'];results=[]
 for row in rows:
  p=ROOT/row['path'];result=dict(row);result['reconciled']=False
  if '/raw-cloud-archives/' in row['path']:
   receipt=private/'raw-migration-receipts'/(p.name.removesuffix('.tar.gz')+'.json');pointer=p.with_name(p.name+'.dvc')
   if receipt.exists() and pointer.exists():
    r=json.loads(receipt.read_text());d=yaml.safe_load(pointer.read_text());ok=r['passed'] and r['verification']['remote_size_and_xet_verified'] and d['outs'][0]['md5']==row['md5']
    result.update(reconciled=bool(ok),classification='cloud_archive_removed_after_preservation',receipt=str(receipt.relative_to(ROOT)),git_commit=r['git_commit'])
  elif row.get('stale'):
   candidate=Path(str(p).replace('/FDS/cases/','/data/').replace('experiments/08_isolated_ember_ignition/experiments/08_isolated_ember_ignition/','experiments/08_isolated_ember_ignition/'))
   if candidate.is_file():
    with candidate.open('rb') as f:md=hashlib.file_digest(f,'md5').hexdigest()
    result.update(reconciled=md==row['md5'],classification='stale_path_exact_hash_match' if md==row['md5'] else 'stale_path_different_bytes',candidate=str(candidate.relative_to(ROOT)),candidate_md5=md)
  results.append(result)
 out={'scope':'Old inventory reconciliation; receipts are existing remote verification evidence, not fresh remote downloads','records':results,'reconciled':sum(x['reconciled'] for x in results),'unresolved':[x for x in results if not x['reconciled']]}
 (private/'missing-output-reconciliation.json').write_text(json.dumps(out,indent=2)+'\n');print('reconciled',out['reconciled'],'unresolved',len(out['unresolved']))
 for x in out['unresolved']:print(x['path'],x.get('classification','needs_review'))
if __name__=='__main__':main()
