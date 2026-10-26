"""Inventory immutable raw archives from verified summaries; does not download or launch."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parent

def main():
 groups=json.loads((R/'active-groups.json').read_text())
 owner={c:g['id'] for g in groups for c in g['cases']}
 frozen=json.loads((R/'results/input-freeze.json').read_text())['cases']
 sources=list((R/'data/summaries').glob('*.json'))
 for d in (R/'data/cloud-collected').glob('*'):
  if (d/'verified.json').exists():sources.extend(d.glob('x36_*.json'))
 sources.extend((R/'data/interrupted').glob('*/x36_*.json'))
 for d in (R/'data/recovery-collected').glob('*'):
  if not (d/'verified.json').exists():continue
  v=json.loads((d/'verified.json').read_text());plan=json.loads((R/'results/partial-recovery-plan.json').read_text()) if v['group']=='x36-density-032-r1' else json.loads((R/v['proof_file']).read_text())
  if 'new_group' not in plan:plan=dict(plan,new_group=plan['group'],reused_completed_cases=plan['excluded_completed_cases'])
  assert v['group']==plan['new_group'] and v['cases']==plan['cases'] and v['cleanup_verified'] and v['all_full_horizon']
  assert not set(v['cases']) & set(plan['reused_completed_cases'])
  for c in v['cases']:
   assert owner[c]==plan['original_group'];owner[c]=v['group'];sources.append(d/(c+'.json'))
 rows={}
 for p in sorted(sources):
  c=p.stem
  if c not in owner:continue
  s=json.loads(p.read_text())
  if 'raw_sha256' not in s:continue
  assert s['result']['full_horizon'] and s['resume']['passed'],p
  assert s['deck_sha256']==frozen[c],p
  assert len(s['raw_sha256'])==64 and s['raw_bytes']>0,p
  row={'case':c,'group':owner[c],'uri':f"gs://tmrw-wildfire-20261015-trial/density36/{owner[c]}/{c}.tar.gz",'sha256':s['raw_sha256'],'bytes':s['raw_bytes'],'summary_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  if c in rows:assert rows[c]['sha256']==row['sha256'] and rows[c]['bytes']==row['bytes'],c
  rows[c]=row
 total=sum(x['bytes'] for x in rows.values());free=shutil.disk_usage(R).free
 report={'cases':len(rows),'expected_cases':len(owner),'bytes':total,'free_local_bytes':free,'raw_content_sha_verified':False,'note':'Expected hashes from completed solver summaries, not yet independent raw-content verification. Raw remains immutable in private GCS. Do not copy the full archive into workspace, DVC cache and local mirror independently without a capacity check.','archives':[rows[c] for c in sorted(rows)]}
 (R/'data/raw-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='archives'}))
if __name__=='__main__':main()
