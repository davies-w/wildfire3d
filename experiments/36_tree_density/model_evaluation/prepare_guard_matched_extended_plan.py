"""Freeze a600-epoch unchanged-model comparison from fit-only convergence evidence."""
from pathlib import Path
import copy,json,hashlib
R=Path(__file__).resolve().parents[1];load=lambda p:json.loads(p.read_text())
old=load(R/'data/guard-matched-pilot01/trial-plan.json');audit=load(R/'results/guard-matched-fit-trajectory.json');assert audit['passed'] and audit['optimizer_updates']==0 and audit['confirmation_and_test_not_used']
assert load(R/'results/guard-matched-pilot01-analysis.json')['passed']
assert not load(R/'results/guard-matched-pilot01-collected.json')['repair_acceptance_passed']
p=copy.deepcopy(old);p['training']['epochs_per_arm']=600
p['trial_identity']=dict(workflow='fds-gpu36-guardmatch02',label='gpu36-guardmatch02',prefix='density36/guard-matched-pilot02/',reservation_key='density36-guard-matched-pilot02')
p['implementation_status']='Same worker/model/loss and actual-CUDA-tested serialized replay as completed pilot01. Fresh matched initialization and optimizer;600 epochs per arm, not warm-starting selected checkpoints.'
p['budget_plan'].update(vm_creation_age_cap_s=1800,task_cap_s=1680,training_soft_cap_s=1560)
p['prior_attempt']=dict(workflow='fds-gpu36-guardmatch01',result='Completed and independently verified but unaccepted. Fit heating improvement increases through300epochs, with9.14percent at300; sampled trajectory does not establish convergence. Selection startup and heating remain below10percent.')
p['evaluation']['winner_rule']='Same selection-only rule and arm tie order as pilot01, extended to600 epochs per arm. Freeze before previously examined development confirmation; never switch using confirmation.'
p['scope']='Longer fitting-budget comparison:600 rather than300 epochs per arm; fresh rerun with identical model, initial weights, seed, data, loss, batch/origin draws, learning rate and unchanged gates. More checkpoint opportunities are an explicit development change. '+old['scope']
p['extension_evidence_sha256']=hashlib.sha256((R/'results/guard-matched-fit-trajectory.json').read_bytes()).hexdigest()
for name,digest in p['source_hashes'].items():assert hashlib.sha256((R/'model_evaluation'/name).read_bytes()).hexdigest()==digest
assert p['acceptance']==old['acceptance'] and p['budget_plan']['maximum_allowance_usd']==1
assert p['training']['epochs_per_arm']==2*old['training']['epochs_per_arm']
(R/'results/guard-matched-extended-trial-plan.json').write_text(json.dumps(p,indent=2)+'\n');print('Extended plan frozen; no training or cloud action')
