"""Inspect the exact cloud archive and bounded workflow without running an optimizer."""
from pathlib import Path
import hashlib,json,tarfile,py_compile
import yaml
R=Path(__file__).resolve().parents[1];D=R/'data/timing-decoder-pilot05';load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=load(R/'results/timing-decoder-pilot05-prepared.json');plan=load(D/'trial-plan.json');pipeline=load(R/'results/joint-pipeline-v2-preflight.json');assert pipeline['passed'];assert sha(D/'inputs.tar')==p['input_sha256'] and sha(D/'workflow.yaml')==p['workflow_sha256']
for name,digest in p['files'].items():assert sha(D/name)==digest,name
with tarfile.open(D/'inputs.tar') as archive:
 members={m.name:m for m in archive.getmembers()};assert set(members)==set(p['files'])|{'hashes.json'}
 for name,digest in p['files'].items():assert members[name].isfile() and hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest
 assert json.load(archive.extractfile('hashes.json'))==p['files']
for name in p['files']:
 if name.endswith('.py'):py_compile.compile(str(D/name),doraise=True)
for kind in ['launch','collect','close','monitor','reconcile','analyze']:py_compile.compile(str(R/'model_evaluation'/f'{kind}_timing_decoder_pilot05.py'),doraise=True)
worker=(D/'worker.py').read_text();assert worker.index("assert torch.cuda.is_available()")<worker.index('torch.optim.AdamW');assert worker.index("save('selection-freeze.json'")<worker.index('d.confirmation_open=True');assert 'max_task_retries' in plan['budget_plan'] and plan['budget_plan']['max_task_retries']==0
assert plan['budget_plan']['maximum_allowance_usd']==.45 and (1125+225)*1.2/3600<=.45
workflow=yaml.safe_load((D/'workflow.yaml').read_text());text=(D/'workflow.yaml').read_text();assert 'gpu36-timing05' in text and 'gas-shape-pilot01' not in text and '1005s' in text
assert plan['arms']==['physical_control','tail_priority'] and plan['training']['epochs_per_arm']==300
# Import and exercise the exact packaged dependencies, without an optimizer.
import sys,torch
sys.path.insert(0,str(D))
from context_data import ContextData
from joint_decoder import JointDecoder
from joint_objective import objective as encoded_objective
from context_objective import objective as physical_objective
torch.set_num_threads(4);data=ContextData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);model=JointDecoder(initial['feature_mean'],initial['feature_std'],data.std,data.scales,'interval',initial['state_mean']);model.load_state_dict(initial['model']);before={k:v.clone() for k,v in model.state_dict().items()};ids=data.roles['fit'][:8];origins=torch.tensor([-1,0,-1,16,-1,74,-1,8]);calibration=load(D/'loss-normalization.json')
for arm in plan['arms']:
 model.zero_grad(set_to_none=True);args=data.training_batch(model,ids,origins)
 loss,parts=physical_objective(*args[:4],data.scales,data.std,*args[4:],**data.objective_metadata(ids,origins),normalization=calibration)
 if arm=='tail_priority':loss=loss+.4*parts['under_tail']
 assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters() if p.requires_grad);assert all(p.grad is None for p in model.parameters() if not p.requires_grad);assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
assert not data.confirmation_open
proof=dict(passed=True,input_sha256=p['input_sha256'],worker_sha256=p['files']['worker.py'],workflow_sha256=p['workflow_sha256'],exact_packaged_both_objectives_derivatives_passed=True,all_archive_members_verified=True,cuda_guard_before_optimizer=True,confirmation_barrier_verified=True,maximum_allowance_usd=.45,optimizer_updates=0,submitted=False)
(R/'results/timing-decoder-pilot05-offline-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
