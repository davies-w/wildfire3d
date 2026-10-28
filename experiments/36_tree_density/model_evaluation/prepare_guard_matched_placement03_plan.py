"""Freeze a placement-only follow-up after exact no-allocation/cleanup proof."""
from pathlib import Path
import copy,json,hashlib
R=Path(__file__).resolve().parents[1];load=lambda p:json.loads(p.read_text())
proof=load(R/'results/guard-matched-pilot02-no-allocation-proof.json');assert proof['passed'] and proof['successful_vm_allocations']==0
assert load(R/'results/guard-matched-pilot02-permission-removed.json')['exact_grant_removed']
assert load(R/'results/guard-matched-pilot02-cleanup.json')==dict(jobs=[],instances=[],disks=[])
p=copy.deepcopy(load(R/'data/guard-matched-pilot02/trial-plan.json'))
p['trial_identity']=dict(workflow='fds-gpu36-guardmatch03',label='gpu36-guardmatch03',prefix='density36/guard-matched-pilot03/',reservation_key='density36-guard-matched-pilot03')
p['prior_attempt']=dict(workflow='fds-gpu36-guardmatch02',result='Cancelled pending after five L4 stockouts in us-east4-a. All observed insert operations completed with errors, no successful VM allocation, no task runtime. Exact grant/resources removed; no accuracy result.')
p['placement']=dict(region='us-east4',zone='us-east4-b',change='Placement only from pilot02; all600epoch scientific settings and deadlines unchanged.')
p['scope']='Placement-only follow-up in us-east4-b after verified unallocated predecessor. '+p['scope']
for name,digest in p['source_hashes'].items():assert hashlib.sha256((R/'model_evaluation'/name).read_bytes()).hexdigest()==digest
(R/'results/guard-matched-placement03-trial-plan.json').write_text(json.dumps(p,indent=2)+'\n');print('Placement-only plan frozen; no cloud action')
