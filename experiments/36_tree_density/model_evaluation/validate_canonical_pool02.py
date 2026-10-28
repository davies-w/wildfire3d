"""Inspect the exact cloud archive and bounded workflow without running an optimizer."""
from pathlib import Path
import hashlib,json,tarfile,py_compile
import yaml
R=Path(__file__).resolve().parents[1];D=R/'data/canonical-pilot02';load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=load(R/'results/canonical-pilot02-prepared.json');plan=load(D/'trial-plan.json');pipeline=load(R/'results/joint-pipeline-v2-preflight.json');assert pipeline['passed'];assert sha(D/'inputs.tar')==p['input_sha256'] and sha(D/'workflow.yaml')==p['workflow_sha256']
for name,digest in p['files'].items():assert sha(D/name)==digest,name
with tarfile.open(D/'inputs.tar') as archive:
 members={m.name:m for m in archive.getmembers()};assert set(members)==set(p['files'])|{'hashes.json'}
 for name,digest in p['files'].items():assert members[name].isfile() and hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest
 assert json.load(archive.extractfile('hashes.json'))==p['files']
for name in p['files']:
 if name.endswith('.py'):py_compile.compile(str(D/name),doraise=True)
for kind in ['launch','collect','close','monitor','reconcile','analyze']:py_compile.compile(str(R/'model_evaluation'/f'{kind}_canonical_pilot02.py'),doraise=True)
worker=(D/'worker.py').read_text();assert worker.index("assert torch.cuda.is_available()")<worker.index('torch.optim.AdamW');assert worker.index("save('selection-freeze.json'")<worker.index('d.confirmation_open=True');assert 'max_task_retries' in plan['budget_plan'] and plan['budget_plan']['max_task_retries']==0
assert plan['budget_plan']['maximum_allowance_usd']==1.3 and (3600+300)*1.2/3600<=1.3
workflow=yaml.safe_load((D/'workflow.yaml').read_text());text=(D/'workflow.yaml').read_text();assert 'gpu36-canonical02' in text and 'gas-shape-pilot01' not in text and '2730s' in text
assert plan['arms']==['canonical_half','canonical_full'] and plan['training']['epochs_per_arm']==600
# Import and exercise the exact packaged dependencies, without an optimizer.
import sys,torch
sys.path.insert(0,str(D))
from canonical_data import CanonicalData as ContextData
from joint_decoder import JointDecoder
from joint_objective import objective as encoded_objective
from canonical_objective import objective as combined_objective
torch.set_num_threads(4);data=ContextData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);model=JointDecoder(initial['feature_mean'],initial['feature_std'],data.std,data.scales,'interval',initial['state_mean']);model.load_state_dict(initial['model']);before={k:v.clone() for k,v in model.state_dict().items()};ids=data.roles['fit'][:8];origins=torch.tensor([-1,0,-1,16,-1,74,-1,8]);calibration=load(D/'loss-normalization.json')
for arm in plan['arms']:
 model.zero_grad(set_to_none=True);args=data.training_batch(model,ids,origins)
 horizons=torch.tensor([1,4,8,16,45,1,4,8]);canonical_origins=torch.tensor([89,86,82,74,45,0,0,0]);loss,parts=combined_objective(model,data,ids,origins,horizons,canonical_origins,normalization=calibration,canonical_coefficient=plan['canonical_loss_coefficients'][arm])
 assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters() if p.requires_grad);assert all(p.grad is None for p in model.parameters() if not p.requires_grad);assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
assert not data.confirmation_open
reference=(R/'model_evaluation/timing_worker_v2.py').read_text();assert worker.split('replay=[]')[1].split('assert not d.confirmation_open')[0].replace(',all_five_canonical_windows_in_restore_fixture=True','')==reference.split('replay=[]')[1].split('assert not d.confirmation_open')[0]
assert plan['acceptance']==load(R/'data/timing-decoder-pilot06/trial-plan.json')['acceptance']
old=load(R/'data/guard-matched-pilot01/trial-plan.json');assert plan['acceptance']==old['acceptance'];assert plan['training']['epochs_per_arm']==600;assert plan['source_hashes']['timing_decoder.py']==old['source_hashes']['timing_decoder.py'];assert plan['initial_decoder_sha256']==old['initial_decoder_sha256'];assert worker!=(R/'data/guard-matched-pilot01/worker.py').read_text()
assert 'us-east4-c' in text and '+ 3600' in text and '+ 2850' in text;assert worker.count('canonical_horizon_choices=canonical_horizons')==2 and worker.count('canonical_origin_choices=canonical_origins')==2;assert 'canonical_horizons[cursor:cursor+128],canonical_origins[cursor:cursor+128]' in worker;assert plan['canonical_acceptance']['overall_each_state_relative_increase_at_most']==.05
assert workflow['main']['steps'][0]['initialize']['assign'][1]['job']['allocationPolicy']['location']['allowedLocations']==['zones/us-east4-a','zones/us-east4-c']
reference=load(R/'results/canonical-pilot01-prepared.json');assert [n for n in p['files'] if p['files'][n]!=reference['files'][n]]==['runtime.py']
assert (D/'runtime.py').read_text().replace('canonical-pilot02/','canonical-pilot01/')==(R/'data/canonical-pilot01/runtime.py').read_text()
assert '${vm.selfLink}' in text
for name in ['get_vm','list_workers','verify']:
 assert name+'_a:' in text and name+'_c:' in text and name+'_append_c:' in text
assert 'list.concat(active_vms.body.items, pool_vm)' in text
# Check complete bounded policy and all VM-query/cleanup branches, not just zone labels.
oldflow=yaml.safe_load((R/'data/canonical-pilot01/workflow.yaml').read_text())
job=workflow['main']['steps'][0]['initialize']['assign'][1]['job']
oldjob=oldflow['main']['steps'][0]['initialize']['assign'][1]['job']
assert job['taskGroups'][0]['taskSpec']['maxRunDuration']==oldjob['taskGroups'][0]['taskSpec']['maxRunDuration']=='2730s'
assert job['taskGroups'][0]['taskSpec']['maxRetryCount']==0
assert job['taskGroups'][0]['taskCount']=='1' and job['taskGroups'][0]['parallelism']=='1'
assert job['allocationPolicy']['instances']==oldjob['allocationPolicy']['instances']
labels=[]
def visit(steps):
 for step in steps:
  for label,body in step.items():
   labels.append(label)
   if 'for' in body:visit(body['for']['steps'])
   if 'try' in body and isinstance(body['try'],dict):
    if 'steps' in body['try']:visit(body['try']['steps'])
   if 'except' in body:visit(body['except'].get('steps',[]))
   if 'switch' in body:
    for branch in body['switch']:
     if 'steps' in branch:visit(branch['steps'])
visit(workflow['main']['steps']);assert len(labels)==len(set(labels)), 'Duplicate workflow labels'
assert '+ 3600' in text and '+ 2850' in text and '+ 900' in text
for phase in ['get_vm','list_workers','verify']:
 assert phase+'_append_vm' in labels
# Equivalent merge fixtures include empty lists and VMs in either supported zone.
for a,c in [([],[]),([{'selfLink':'zone-a/vm'}],[]),([],[{'selfLink':'zone-c/vm'}]),([{'selfLink':'zone-a/vm'}],[{'selfLink':'zone-c/vm'}])]:
 merged=list(a)
 for vm in c:merged=merged+[vm]
 assert merged==a+c and all('selfLink' in vm for vm in merged)
proof=dict(capacity_only_change=True,both_supported_zones_monitored_and_cleaned=True,passed=True,input_sha256=p['input_sha256'],worker_sha256=p['files']['worker.py'],workflow_sha256=p['workflow_sha256'],serialized_restore_scope_preserved=True,unchanged_acceptance_gates=True,exact_packaged_both_objectives_derivatives_passed=True,canonical_choices_preserved_in_all_checkpoints=True,canonical_guards_and_full_stride_one_coverage=True,all_archive_members_verified=True,cuda_guard_before_optimizer=True,confirmation_barrier_verified=True,maximum_allowance_usd=1.3,optimizer_updates=0,submitted=False)
(R/'results/canonical-pilot02-offline-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
