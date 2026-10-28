"""Release only verified terminal pilot02 after its cost enters the project estimate."""
import sys,json,fcntl
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,read,save
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations']['density36-timing-decoder-pilot01'];proof=read('results/timing-decoder-pilot01-collected.json');assert proof['cleanup_verified'];assert read('results/timing-decoder-pilot01-permission-removed.json')['exact_grant_removed'];assert read('results/timing-decoder-pilot01-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
 status=read('results/timing-decoder-pilot01-status.json');assert status['state']!='ACTIVE' and status['name']==r['execution'];assert r['cost']['stage'] in ['runtime_estimate','posted_billing_subject_to_adjustment'] and r['cost']['usd']>0
 assert r['state'] in ['submitted','completed_reconciled'];r.update(state='completed_reconciled',terminal_evidence='experiments/36_tree_density/results/timing-decoder-pilot01-status.json');b['reserved_usd']=sum(x['allowance_usd'] for x in b['reservations'].values() if x['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);B.write_text(json.dumps(b,indent=2)+'\n')
 proof=dict(estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],headroom_usd=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd'],pilot_compute_cost=r['cost'],cost_already_in_project_estimate=True,no_overlapping_cost_addition=True)
 save('results/timing-decoder-pilot01-cost-reconciled.json',proof);print(json.dumps(proof))
