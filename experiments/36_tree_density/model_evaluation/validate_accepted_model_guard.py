"""Exercise final-test refusal conditions on synthetic metadata/checkpoints only."""
from pathlib import Path
import copy,hashlib,json,tempfile
import torch
from accepted_model_guard import require_accepted_model
R=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='canonical-final-guard-') as folder:
 root=Path(folder);(root/'results').mkdir();outputs=root/'data/canonical-pilot01-results';outputs.mkdir(parents=True);state={'fixture':torch.tensor([1.,2.])};digest=hashlib.sha256(state['fixture'].numpy().tobytes()).hexdigest();checkpoint=dict(model=state,epoch=10,apply_decoder=True)
 records={'results/canonical-pilot01-analysis.json':dict(passed=True,repair_acceptance_passed=True,selection_and_winner_independently_reconstructed=True,test_evaluated=False,optimizer_updates=0,winner='fixture'),'results/canonical-pilot01-collected.json':dict(passed=True,experiment_complete=True,cleanup_verified=True),'results/canonical-pilot01-permission-removed.json':dict(exact_grant_removed=True),'data/canonical-pilot01-results/selection-freeze.json':dict(winner='fixture',confirmation_scored=False,test_evaluated=False,arms=[dict(arm='fixture',accepted_on_selection=True,apply_decoder=True,epoch=10,model_sha256=digest)]),'data/canonical-pilot01-results/comparison.json':dict(winner='fixture',passed=True,checks={'fixture':True},test_evaluated=False),'data/canonical-pilot01-results/complete.json':dict(passed=True,repair_acceptance_passed=True,selection_frozen_before_confirmation=True,test_evaluated=False)}
 def reset():
  for name,value in records.items():(root/name).write_text(json.dumps(value))
  torch.save(checkpoint,outputs/'fixture-selected.pt')
 reset();positive=require_accepted_model(root);assert positive['model_sha256']==digest
 cases=[('results/canonical-pilot01-analysis.json','repair_acceptance_passed',False),('results/canonical-pilot01-analysis.json','selection_and_winner_independently_reconstructed',False),('results/canonical-pilot01-analysis.json','test_evaluated',True),('results/canonical-pilot01-collected.json','experiment_complete',False),('results/canonical-pilot01-permission-removed.json','exact_grant_removed',False),('data/canonical-pilot01-results/comparison.json','passed',False),('data/canonical-pilot01-results/complete.json','test_evaluated',True)]
 rejected=[]
 for name,key,value in cases:
  reset();r=copy.deepcopy(records[name]);r[key]=value;(root/name).write_text(json.dumps(r));blocked=False
  try:require_accepted_model(root)
  except AssertionError:blocked=True
  assert blocked;rejected.append([name,key])
 reset();r=copy.deepcopy(records['data/canonical-pilot01-results/selection-freeze.json']);r['arms'][0]['accepted_on_selection']=False;(outputs/'selection-freeze.json').write_text(json.dumps(r));blocked=False
 try:require_accepted_model(root)
 except AssertionError:blocked=True
 assert blocked;rejected.append('selection_rejected')
 reset();bad=copy.deepcopy(checkpoint);bad['model']['fixture'][0]=9;torch.save(bad,outputs/'fixture-selected.pt');blocked=False
 try:require_accepted_model(root)
 except AssertionError:blocked=True
 assert blocked;rejected.append('checkpoint_state_changed')
source=(R/'model_evaluation/run_canonical_final_inference.py').read_text();assert source.index('accepted=require_accepted_model')<source.index("with freeze.open('x')")<source.index("source=np.load")
out=dict(passed=True,synthetic_guard_cases_rejected=len(rejected),positive_synthetic_identity_verified=True,actual_guard_precedes_model_freeze_and_test_array_loading=True,optimizer_updates=0,original_test_not_loaded=True,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['accepted_model_guard.py','run_canonical_final_inference.py','validate_accepted_model_guard.py']},scope='Synthetic metadata and a two-value fixture checkpoint in a temporary directory only. No scientific model accepted or evaluated; no original test targets loaded.')
(R/'results/accepted-model-guard-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
