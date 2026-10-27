"""Identity-only model workload audit; never fits or launches a model."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[1]
OLD=R.parent/'35_surrogate_diagnostics/attempt25'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def updates(rotations,plan,epochs):
 total=0
 for rot in rotations:
  for epoch in range(1,epochs+1):
   h=next(x['steps'] for x in reversed(plan['horizon_curriculum']) if epoch>=x['first_epoch'])
   total+=math.ceil(len(rot['train'])*math.ceil(90/h)/plan['batch_windows'])
 return total

def main():
 folds=json.loads((R/'data/grouped-folds.json').read_text())
 old=json.loads((OLD/'schema.json').read_text())
 plan=json.loads((OLD/'coverage-plan.json').read_text())
 worker=(OLD/'worker.py').read_text()
 assert len(folds['rotations'])==10 and folds['histories']==2080
 required=["assert external.shape==(520,90,9)","weights=torch.zeros(520,90,device=device)","assert len(reports)==8","folds=8)","rotation['training_fold_count']"]
 assert all(x in worker for x in required)
 report={'status':'offline planning only; not launch preflight approval','training_launched':False,
 'source_worker_sha256':digest(OLD/'worker.py'),'source_model_sha256':digest(OLD/'model.py'),
 'source_plan_sha256':digest(OLD/'coverage-plan.json'),'fold_manifest_sha256':digest(R/'data/grouped-folds.json'),
 'histories':2080,'rotations':10,'train_histories':[len(r['train']) for r in folds['rotations']],
 'unchanged_recipe':{k:plan[k] for k in ('architecture','learning_rate','batch_windows','minimum_epochs','epochs_max','patience_epochs','horizon_curriculum','thermal_loss','training_balance','burn_in','evaluation_horizons')},
 'required_adaptations':['Assert 2080 histories and allocate matching weights','Require ten selected reports and ten completed tests','Set training_fold_count=8 in each derived rotation without altering frozen fold assignments','Replace nested learning-curve labels with grouped ten-fold evaluation scope','Freeze all ten validation selections before opening any tests'],
 'optimizer_updates_if_all_models_run_same_epochs':{str(e):{'new':updates(folds['rotations'],plan,e),'prior_nested_eight':updates(old['rotations'],plan,e)} for e in (100,400)},
 'runtime_limitations':'Update counts are not wall-time estimates: recurrent horizons, prefix recomputation, full train/validation evaluation every epoch, all-origin test forecasts and checkpoint uploads also cost time. Do not reuse prior three-hour deadline without a measured cloud timing and checkpoint plan.',
 'launch_requirements':['All 1560 new archives and four-state histories verified, 2080-history merge complete','CPU data-leakage, normalization, shape, prefix and report checks without local optimization','Cloud CUDA determinism/backward32 and complete evaluation checks before fitting','Measured runtime projection and bounded deadlines within existing $8 reservation; preserve every epoch and optimizer/RNG resume','All selections frozen before test evaluation; no test-driven retries'],
 'interpretation':'More data changes optimizer updates per epoch. This is the same learning recipe, not a compute-matched information-only comparison. Previously examined reshuffled data is not pristine.'}
 (R/'results/model-workload-plan.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report['optimizer_updates_if_all_models_run_same_epochs']))
if __name__=='__main__':main()
