"""Release measured terminal preflight allowances; keep active training reserved."""
from pathlib import Path
import fcntl,json
R=Path(__file__).resolve().parents[1];B=R.parent/'33_representation_loss/budget.json'
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());released=[]
 for suffix in ['01','02','03']:
  stem='model-timing'+('' if suffix=='01' else suffix);key='density36-model-preflight'+suffix;r=b['reservations'][key]
  if r['state']=='completed_reconciled':continue
  assert r['state']=='submitted' and r['cost']['stage'] in ['runtime_estimate','posted_billing_subject_to_adjustment']
  assert json.loads((R/'results'/f'{stem}-cleanup.json').read_text())=={'jobs':[],'instances':[],'disks':[]}
  status=json.loads((R/'results'/f'{stem}-status.json').read_text());assert status['state'] in ['SUCCEEDED','FAILED'] and status['name']==r['execution']
  r.update(state='completed_reconciled',terminal_evidence=str(Path('experiments/36_tree_density/results')/f'{stem}-status.json'));released.append(key)
 b['reserved_usd']=sum(r['allowance_usd'] for r in b['reservations'].values() if r['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue'])
 assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd'];B.write_text(json.dumps(b,indent=2)+'\n')
 (R/'results/model-preflight-cost-reconciliation.json').write_text(json.dumps({'released':released,'estimate_usd':b['estimated_spend_usd'],'reserved_usd':b['reserved_usd'],'training_reservation_unchanged':b['reservations']['density36-learning'],'note':'Costs already in project estimate, not added again; historical allowances retained.'},indent=2)+'\n')
