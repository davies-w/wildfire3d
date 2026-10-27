"""Screen saved validation logs only; do not change checkpoint selection."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def main():
 D=R/'data/pair-sequence-r0-results';base=json.loads((D/'fold01-epoch183.json').read_text())['validation']['rollout'];rows=[]
 for p in D.glob('fold01-epoch*.json'):
  d=json.loads(p.read_text());v=d['validation']['rollout'];rows.append({'epoch':d['epoch'],'objective_ratio':v['objective']/base['objective'],'physical_MAE_ratios':[x/y for x,y in zip(v['physical_MAE_by_feature'],base['physical_MAE_by_feature'])],'gas_peak_MAE_ratio':v['peak_release_MAE_kg_s']/base['peak_release_MAE_kg_s'],'ignition_gas_MAE_ratio':v['physical_MAE_by_window']['ignition'][2]/base['physical_MAE_by_window']['ignition'][2]})
 eligible=[r for r in rows if r['objective_ratio']<=1.05 and max(r['physical_MAE_ratios'])<=1.05];ranked=sorted(eligible,key=lambda r:r['ignition_gas_MAE_ratio']);proof={'scope':'Saved validation logs only. Proxy ignitionMAE through20s is not the frozen startup-p90 criterion through32s. No test outcomes, no checkpoint selection changes.','baseline_epoch':183,'eligible_original_validation_and_each_state_within5percent':len(eligible),'top_proxy_candidates':ranked[:8],'all':sorted(rows,key=lambda r:r['epoch'])};(R/'results/exposure-existing-checkpoint-screen.json').write_text(json.dumps(proof,indent=2)+'\n');print('Eligible checkpoints:',len(eligible),'best ignition MAE ratio:',ranked[0]['ignition_gas_MAE_ratio'])
if __name__=='__main__':main()
