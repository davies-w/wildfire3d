"""Offline package/limits audit; never execute a training batch or optimizer."""
from pathlib import Path
import ast,hashlib,json,tarfile,yaml
R=Path(__file__).resolve().parents[1];D=R/'data/gas-shape-pilot01';p=json.loads((R/'results/gas-shape-pilot01-prepared.json').read_text());plan=json.loads((D/'pilot-plan.json').read_text());assert json.loads((R/'results/gas-head-candidate-preflight.json').read_text())['passed'];assert json.loads((R/'results/gas-head-metrics-preflight.json').read_text())['passed']
assert json.loads((R/'results/gas-shape-selection-preflight.json').read_text())['passed'];assert json.loads((R/'results/gas-shape-head-preflight.json').read_text())['passed'];assert plan['shape_head_sha256']==p['files']['gas_shape_head.py']
for name,h in p['files'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h
assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256'];assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
with tarfile.open(D/'inputs.tar') as tar:
 hashes=json.load(tar.extractfile('hashes.json'));assert hashes==p['files'];assert set(tar.getnames())==set(p['files'])|{'hashes.json'}
 for name,h in hashes.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==h
w=yaml.safe_load((D/'workflow.yaml').read_text());assign=w['main']['steps'][0]['initialize']['assign'];task=assign[1]['job']['taskGroups'][0]['taskSpec'];assert task['maxRetryCount']==0 and task['maxRunDuration']=='1350s';s=(D/'workflow.yaml').read_text();assert '+ 1500' in s and '+ 3600' in s and '+ 900' in s and 'us-central1-a' in s;assert plan['budget_plan']['vm_creation_age_cap_s']/3600*plan['budget_plan']['maximum_rate_bound_usd_per_hour']<=p['maximum_allowance_usd']==.4
worker=(D/'worker.py').read_text();tree=ast.parse(worker);compile(tree,'worker.py','exec');assert "assert torch.cuda.is_available()" in worker and "No local training" in worker;assert worker.index('assert torch.cuda.is_available()')<worker.index('torch.optim.AdamW')
for fragment in ['next_update_bitwise_equal=True','nonempty_optimizer=True','batch_cursor=cursor','permutation=order','history=history','best_state=best_state','automatic_retry=False',"save('selection-freeze.json'",'torch.isfinite(loss)',"arm=='peak_aware'",'corrected_gas_feedback']:
 if fragment=='corrected_gas_feedback':assert plan['training'][fragment] is False
 else:assert fragment in worker,fragment
assert 'and selection_key(row)<best' in worker and 'eligible(baseline,' in worker and 'times[ids])' in worker
assert worker.index("save('selection-freeze.json'")<worker.index("save('comparison.json'");assert "for ep in range(1,P['training']['epochs_per_arm']+1)" in worker
for name in ['launch_gas_shape_pilot01.py','collect_gas_shape_pilot01.py','close_gas_shape_pilot01.py','reconcile_gas_shape_pilot01.py']:compile((R/'model_evaluation'/name).read_text(),name,'exec')
proof=dict(passed=True,worker_sha256=p['files']['worker.py'],files_verified=len(p['files']),archive_hashes_exact=True,cloud_CUDA_guard_before_optimizer=True,runtime_allowance_bounded=True,matched_control_and_primary=True,checkpoint_and_selection_freeze_structure_verified=True,baseline_metric_replay_passed=True,local_optimizer_updates=0,test_evaluated=False,scope='Offline source/package checks only. Actual CUDA optimizer replay and numerical training checks must pass in worker. No candidate accuracy claim or launch.')
# Write proof only after the exact packaged-head replay below passes.

# Replay the exact packaged initial head, not a separately initialized probe.
import sys,numpy as np,torch
sys.path.insert(0,str(D));from gas_shape_head import GasShapeHead
torch.set_num_threads(4);a=np.load(D/'features.npz');c=json.loads((D/'candidate-plan.json').read_text());ck=torch.load(D/'initial-head.pt',map_location='cpu',weights_only=False);head=GasShapeHead(ck['feature_mean'],ck['feature_std']);head.load_state_dict(ck['model']);idx=c['train_indices'][:64];x=torch.tensor(a['features'][idx]);base=torch.tensor(a['base_states'][idx,:,2]);times=torch.tensor(a['time'][idx]);out=head(x,base,times);assert torch.equal(out,base);loss=(out-torch.tensor(a['truth'][idx,1:,2])).square().mean();loss.backward();assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in head.parameters());assert head.net[-1].weight.grad.norm()>0;proof.update(exact_packaged_initial_head_baseline_equal=True,exact_packaged_initial_head_gradient_finite_nonzero=True);(R/'results/gas-shape-pilot01-offline-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print('Exact packaged initial head replay/isolated gradient passed; no optimizer')
