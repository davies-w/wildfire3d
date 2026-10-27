"""Conservative timing-derived training projection, without fitting or submission."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-timing-collected.json').read_text())['passed']
 t=json.loads((R/'data/model-timing-results/timing.json').read_text());folds=json.loads((R/'data/grouped-folds.json').read_text())
 rates={h:max(x['seconds'] for x in t['batches'] if x['horizon']==h) for h in (1,8,16,32)}
 projections={}
 for epochs in (100,400):
  batches={h:0 for h in rates}
  for rot in folds['rotations']:
   for epoch in range(1,epochs+1):
    h=1 if epoch<=20 else 8 if epoch<=40 else 16 if epoch<=60 else 32
    batches[h]+=math.ceil(len(rot['train'])*math.ceil(90/h)/256)
  measured=sum(batches[h]*rates[h] for h in rates)+10*epochs*t['train_validation_evaluation_seconds']
  # Independent reserves for immutable per-epoch checkpoint/JSON uploads and test forecasts.
  margin=2*measured+10*epochs*2+1800
  projections[str(epochs)]={'updates_by_horizon':batches,'measured_component_seconds':measured,'conservative_seconds':margin,'hours':margin/3600}
 report={'timing_only_no_accuracy':True,'batch_seconds_upper_observed':rates,'evaluation_seconds_per_epoch':t['train_validation_evaluation_seconds'],'projections':projections,'limitations':['Only one timing batch per origin/horizon; cold start and GPU variability remain','Batch timing excludes AdamW updates, included indirectly in2x compute margin','Two seconds per epoch reserved for JSON/checkpoint transfers; network stalls can exceed this','Thirty minutes reserved for selected all-origin forecasts, initialization and final reports','Patience can stop before400epochs; estimate is not a completion guarantee'],'model_allowance_remaining_usd':7.5,'training_started':False}
 (R/'results/model-training-runtime-plan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
