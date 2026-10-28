"""Verify a narrowly scoped restore correction against the actual failed CUDA task; no optimization."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1];oldpath=R/'model_evaluation/timing_worker.py';newpath=R/'model_evaluation/timing_worker_v2.py';old=oldpath.read_text();new=newpath.read_text();root=R/'data/timing-decoder-pilot05-results';trace=(root/'bootstrap-error.txt').read_text();job=json.loads((root/'job-status.json').read_text());collected=json.loads((R/'results/timing-decoder-pilot05-collected.json').read_text())
assert job['status']['state']=='FAILED' and not collected['experiment_complete'] and collected['cleanup_verified'];assert 'Expected all tensors to be on the same device' in trace and 'worker.py", line 45' in trace
assert hashlib.sha256(oldpath.read_bytes()).hexdigest()==hashlib.sha256((R/'data/timing-decoder-pilot05/worker.py').read_bytes()).hexdigest();assert not list(root.glob('*-epoch*.pt'))
marker='\nreplay=[]\n';tail='assert not d.confirmation_open\nbaseline='
assert old.split(marker)[0]==new.split(marker)[0], 'Model, loss, optimizer setup or train_batch changed'
assert old.split(tail)[1]==new.split(tail)[1], 'Fitting, selection, checkpoints or confirmation changed'
oldmid=old.split(marker)[1].split(tail)[0];newmid=new.split(marker)[1].split(tail)[0]
assert oldmid.count('train_batch(')==newmid.count('train_batch(')==3
prefix=oldmid.split("    for key,value in o.state_dict()['state'].items():")[0].replace('snap=torch.load(buffer,map_location=device,weights_only=False)',"snap=torch.load(buffer,map_location='cpu',weights_only=False)")
assert prefix==newmid.split('    restored_opt=o.state_dict();')[0]
for check in ["restored_opt['param_groups']==expected_opt['param_groups']","set(restored_opt['state'])==set(expected_opt['state'])","set(value)==set(expected_opt['state'][key])","v.device==other.device","v.dtype==other.dtype","torch.equal(v,other)","serialized_restore_map_location='cpu'","optimizer_device_layout_preserved=True"]:assert check in newmid,check
ast.parse(new)
proof=dict(passed=True,failed_execution=json.loads((R/'results/timing-decoder-pilot05-execution.json').read_text())['name'],failed_task_seconds=float(job['status']['runDuration'].removesuffix('s')),failure_stage='First arm discarded serialized optimizer preflight, before fitted epoch loop',old_source_sha256=hashlib.sha256(old.encode()).hexdigest(),new_source_sha256=hashlib.sha256(new.encode()).hexdigest(),trace_sha256=hashlib.sha256(trace.encode()).hexdigest(),model_next_update_assertion_preceded_failure=True,fit_epochs=0,preflight_updates_per_arm_unchanged=3,all_fit_loss_sampling_selection_checkpoint_confirmation_code_identical=True,strict_optimizer_keys_groups_device_dtype_values_enforced=True,restore_map_location='cpu',actual_cuda_replay_passed=False,optimizer_updates_on_local_cpu=0,limitations='Source-scope verification and actual failure diagnosis only. CPU loading lets PyTorch place model parameters and optimizer moments while retaining CPU scalar step counters. Both-arm serialized replay/device/value checks still must pass on actual CUDA; no model accuracy evidence.')
(R/'results/timing-restore-repair-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
