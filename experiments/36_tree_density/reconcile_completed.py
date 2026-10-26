"""Release only terminal compute allowances with cleanup and measured-cost evidence."""
from pathlib import Path
import datetime,fcntl,json
R=Path(__file__).resolve().parent;B=R.parent/'33_representation_loss/budget.json'
def main():
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());rows=[]
  for key,res in b['reservations'].items():
   if not key.startswith('x36-') or res['state'] not in ('submitted','delegated_to_cloud_queue'):continue
   if res.get('cost',{}).get('stage') not in ('runtime_estimate','posted_billing_subject_to_adjustment'):continue
   proofs=[(R/'jobs'/key/'completion.json',R/'jobs'/key/'cleanup.json'),(R/'data/cloud-collected'/key/'verified.json',R/'data/cloud-collected'/key/'cleanup.json')]
   for proof,clean in proofs:
    if not proof.exists() or not clean.exists():continue
    p=json.loads(proof.read_text());c=json.loads(clean.read_text())
    if not p.get('cleanup_verified') or c!={'instances':[],'disks':[],'jobs':[]}:continue
    res['state']='completed_reconciled';res['historical_allowance_usd']=res['allowance_usd'];res['terminal_evidence']=str(proof.relative_to(R.parent.parent));rows.append(key);break
  active=('reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue')
  b['reserved_usd']=sum(r['allowance_usd'] for r in b['reservations'].values() if r['state'] in active)
  assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
  B.write_text(json.dumps(b,indent=2)+'\n')
  report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'released_groups':rows,'reserved_usd':b['reserved_usd'],'estimated_spend_usd':b['estimated_spend_usd'],'note':'Historical allowances retained; costs already included in project estimate, never added again. Unmeasured or nonterminal reservations unchanged.'}
  (R/'results/completed-cost-reconciliation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
