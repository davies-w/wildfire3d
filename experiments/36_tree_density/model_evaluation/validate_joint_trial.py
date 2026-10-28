"""Inspect the exact cloud archive and bounded workflow without running an optimizer."""
from pathlib import Path
import hashlib,json,tarfile,py_compile
import yaml
R=Path(__file__).resolve().parents[1];D=R/'data/joint-decoder-pilot01';load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=load(R/'results/joint-decoder-pilot01-prepared.json');plan=load(D/'trial-plan.json');pipeline=load(R/'results/joint-pipeline-preflight.json');assert pipeline['passed'];assert sha(D/'inputs.tar')==p['input_sha256'] and sha(D/'workflow.yaml')==p['workflow_sha256']
for name,digest in p['files'].items():assert sha(D/name)==digest,name
with tarfile.open(D/'inputs.tar') as archive:
 members={m.name:m for m in archive.getmembers()};assert set(members)==set(p['files'])|{'hashes.json'}
 for name,digest in p['files'].items():assert members[name].isfile() and hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest
 assert json.load(archive.extractfile('hashes.json'))==p['files']
for name in p['files']:
 if name.endswith('.py'):py_compile.compile(str(D/name),doraise=True)
for kind in ['launch','collect','close','monitor','reconcile','analyze']:py_compile.compile(str(R/'model_evaluation'/f'{kind}_joint_decoder_pilot01.py'),doraise=True)
worker=(D/'worker.py').read_text();assert worker.index("assert torch.cuda.is_available()")<worker.index('torch.optim.AdamW');assert worker.index("save('selection-freeze.json'")<worker.index('d.confirmation_open=True');assert 'max_task_retries' in plan['budget_plan'] and plan['budget_plan']['max_task_retries']==0
assert plan['budget_plan']['maximum_allowance_usd']==.25 and (900+225)*.8/3600<=.25
workflow=yaml.safe_load((D/'workflow.yaml').read_text());text=(D/'workflow.yaml').read_text();assert 'gpu36-joint01' in text and 'gas-shape-pilot01' not in text and '780s' in text
assert plan['arms']==['direct','interval'] and plan['training']['epochs_per_arm']==300
proof=dict(passed=True,input_sha256=p['input_sha256'],worker_sha256=p['files']['worker.py'],workflow_sha256=p['workflow_sha256'],all_archive_members_verified=True,cuda_guard_before_optimizer=True,confirmation_barrier_verified=True,maximum_allowance_usd=.25,optimizer_updates=0,submitted=False)
(R/'results/joint-decoder-pilot01-offline-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
