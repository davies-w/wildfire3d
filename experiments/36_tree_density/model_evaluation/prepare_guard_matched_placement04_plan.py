"""Prepare only after supported-zone evidence and full closure of the rejected placement."""
from pathlib import Path
import copy,json,hashlib
R=Path(__file__).resolve().parents[1];load=lambda p:json.loads(p.read_text())
proof=load(R/'results/guard-matched-pilot03-no-allocation-proof.json');assert proof['passed'] and proof['successful_vm_allocations']==0
assert load(R/'results/guard-matched-pilot03-permission-removed.json')['exact_grant_removed'];assert load(R/'results/guard-matched-pilot03-cleanup.json')==dict(jobs=[],instances=[],disks=[])
support=load(R/'results/guard-matched-east4-machine-support.json');matches=[m for m in support if m['zone'].endswith('us-east4-c')];assert len(matches)==1 and matches[0]['name']=='g2-standard-4' and matches[0]['accelerators']==[dict(guestAcceleratorCount=1,guestAcceleratorType='nvidia-l4')]
p=copy.deepcopy(load(R/'data/guard-matched-pilot03/trial-plan.json'));p['trial_identity']=dict(workflow='fds-gpu36-guardmatch04',label='gpu36-guardmatch04',prefix='density36/guard-matched-pilot04/',reservation_key='density36-guard-matched-pilot04')
p['prior_attempt']=dict(workflow='fds-gpu36-guardmatch03',result='Batch rejected unsupported g2-standard-4 in us-east4-b before scheduling; no task runtime or VM insert requests. Resources/grant removed and reservation reconciled. This was a placement preflight omission, not an accuracy result.')
p['placement']=dict(region='us-east4',zone='us-east4-c',change='Placement only; all600epoch scientific settings and deadlines unchanged. G2-standard-4/L4 support verified from live catalog; launch must re-describe exact machine type. Capacity still not guaranteed.')
p['placement_support_sha256']=hashlib.sha256((R/'results/guard-matched-east4-machine-support.json').read_bytes()).hexdigest()
p['scope']='Placement-only follow-up in verified supported us-east4-c. '+load(R/'data/guard-matched-pilot02/trial-plan.json')['scope']
for name,digest in p['source_hashes'].items():assert hashlib.sha256((R/'model_evaluation'/name).read_bytes()).hexdigest()==digest
(R/'results/guard-matched-placement04-trial-plan.json').write_text(json.dumps(p,indent=2)+'\n');print('Supported-zone plan frozen; no cloud action')
