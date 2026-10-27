"""Close measured first-pair/zero-runtime allocation reservation, without double counting."""
from pathlib import Path
import json,fcntl
R=Path(__file__).resolve().parents[1];B=R.parent/'33_representation_loss/budget.json'
assert json.loads((R/'results/pair-sequence-r0-collected.json').read_text())['passed']
a=json.loads((R/'results/pair-rotation1-capacity-a-stockout.json').read_text());assert not any(a['cleanup'].values()) and a['job']['status']['runDuration']=='0s'
c=json.loads((R/'results/pair-rotation1-stockout.json').read_text());assert c['job']['status']['runDuration']=='0s'
rows=json.loads((R.parents[1]/'docs/billing-audit-2026-10-23/vm-runtime.json').read_text());matched=[x for x in rows if x['trial_id']=='gpu36-seq01-r0'];assert len(matched)==1 and matched[0]['end']
assert not [x for x in rows if x['trial_id'] in ('gpu36-seq01-r1','gpu36-seq01-r1a')]
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations']['density36-pair-sequence01'];assert r['state'] in ('submitted','completed_reconciled')
 assert b['accounting']['as_of_utc']>='2026-10-27T17:47:00' and b['estimated_spend_usd']>=46
 r.update(state='completed_reconciled',cost=dict(stage='runtime_estimate',usd=sum(x['estimated_compute_usd'] for x in matched),vm_hours=sum(x['hours'] for x in matched),resources=[x['vm'] for x in matched]),terminal_evidence='Both rotation1 allocation attempts zero runtime and empty cleanup; rotation0 collected PASS',cost_already_in_project_estimate=True)
 b['reserved_usd']=sum(x['allowance_usd'] for x in b['reservations'].values() if x['state'] in ('reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue'));B.write_text(json.dumps(b,indent=2)+'\n')
 p=dict(estimate=b['estimated_spend_usd'],reserved=b['reserved_usd'],headroom=125-b['estimated_spend_usd']-b['reserved_usd'],first_pair_compute=r['cost'],zero_runtime_attempts=['gpu36-seq01-r1','gpu36-seq01-r1a'],no_pending_compute=True)
 (R/'results/pair-sequence-cost-reconciled.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(p))
