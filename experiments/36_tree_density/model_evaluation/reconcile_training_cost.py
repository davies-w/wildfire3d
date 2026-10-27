"""Release only the measured completed baseline training reservation."""
from pathlib import Path
import fcntl,json
R=Path(__file__).resolve().parents[1];B=R.parent/'33_representation_loss/budget.json'
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations']['density36-learning']
 assert json.loads((R/'results/model-training-collected.json').read_text())['passed']
 assert json.loads((R/'results/model-training-cleanup.json').read_text())=={'jobs':[],'instances':[],'disks':[]}
 status=json.loads((R/'results/model-training-status.json').read_text());assert status['state']=='SUCCEEDED' and status['name']==r['execution']
 assert r['cost']['stage'] in ['runtime_estimate','posted_billing_subject_to_adjustment'] and r['cost']['usd']>0
 assert r['state'] in ['submitted','completed_reconciled'];r.update(state='completed_reconciled',terminal_evidence='experiments/36_tree_density/results/model-training-status.json')
 b['reserved_usd']=sum(x['allowance_usd'] for x in b['reservations'].values() if x['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue'])
 B.write_text(json.dumps(b,indent=2)+'\n')
 proof={'estimate_usd':b['estimated_spend_usd'],'reserved_usd':b['reserved_usd'],'headroom_usd':b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd'],'baseline_compute_cost':r['cost'],'cost_already_in_project_estimate':True}
 (R/'results/model-training-cost-reconciled.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
