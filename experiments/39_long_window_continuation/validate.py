"""Offline shape, lineage and control-flow checks; never runs an optimizer."""
from pathlib import Path
import ast, hashlib, json, math
import numpy as np
import torch, yaml
R=Path(__file__).resolve().parent;D=R/'data/training'
p=json.loads((D/'coverage-plan.json').read_text());a=np.load(D/'data/sequences.npz');steps=a['state'].shape[1]-1
assert steps==90 and a['state'].shape[0]==2080
ck=torch.load(D/'data/resume/fold00.pt',map_location='cpu',weights_only=False)
assert ck['epoch']==ck['best_epoch']==109 and ck['optimizer']['state'] and ck['rng']
assert ck['schema_hash']==hashlib.sha256((D/'schema.json').read_bytes()).hexdigest()
assert hashlib.sha256((D/'data/resume/fold00.pt').read_bytes()).hexdigest()==p['continuation']['checkpoint_sha256']
assert p['horizon_curriculum'][-2:]==[{'first_epoch':110,'steps':64},{'first_epoch':130,'steps':90}]
assert p['minimum_epochs']==160 and p['epochs_max']==400
for h,count in [(64,44874),(90,1662)]:
 windows=[(n,j) for n in range(1662) for j in range(91-h)]
 assert len(windows)==count and all(j+h<=90 for n,j in windows)
 if h==90:assert all(j==0 for n,j in windows)
 assert math.ceil(count/256)==(176 if h==64 else 7)
w=(D/'worker.py').read_text();assert 'elif epoch>61' not in w and 'if epoch in [21,41,61]' not in w
assert 'TRAINING_SOFT_SECONDS' in w and 'torch.cuda.is_available()' in w
for f in D.rglob('*.py'):ast.parse(f.read_text())
for n,h in json.loads((D/'hashes.json').read_text()).items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
pool=yaml.safe_load((R/'pool.yaml').read_text());cs=pool['main']['steps'][0]['initialize']['assign'][0]['candidates'];assert len(cs)==3
for c in cs:
 t=c['job']['taskGroups'][0]['taskSpec'];policy=c['job']['allocationPolicy']['instances'][0]['policy']
 assert policy['provisioningModel']=='SPOT' and policy['accelerators']==[{'type':'nvidia-tesla-t4','count':1}]
 assert t['maxRetryCount']==0 and t['maxRunDuration']=='49500s'
 assert t['environment']['variables']['CANDIDATE_ID']==c['id']
assert 'losers_cleanup_verified' in (D/'bootstrap.py').read_text()
assert not (D/'data/resume/fold00-report.json').exists()
print('PASS: checkpoint109, 64/90 windows, epoch160 minimum, cloud-only gate, three Spot T4 candidates; no optimizer executed')
