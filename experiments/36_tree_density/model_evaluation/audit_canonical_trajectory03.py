"""Posthoc diagnosis of frozen selection trajectories; no new fitting or test use."""
from pathlib import Path
import json,sys,hashlib
R=Path(__file__).resolve().parents[1];D=R/'data/canonical-pilot03';O=R/'data/canonical-pilot03-results';sys.path.insert(0,str(D))
from canonical_metrics import checks,guarded
load=lambda p:json.loads(p.read_text())
assert load(R/'results/canonical-pilot03-analysis.json')['passed']
plan=load(D/'trial-plan.json');baseline=load(O/'selection-baseline.json');scales=load(D/'candidate-plan.json').get('physical_scales')
# Match the exact scales used by the independent replay without importing test arrays.
from canonical_data import CanonicalData
scales=CanonicalData(D).scales.tolist();arms={}
def summary(metrics):
 result={}
 for regime in ['display','autonomous']:
  b,c=baseline[regime],metrics[regime]
  result[regime]=dict(state_MAE_relative_reduction=[1-y/x if x else None for x,y in zip(b['physical_MAE_by_feature'],c['physical_MAE_by_feature'])],startup_p90_relative_reduction=1-c['startup_gas_p90_deficit']/b['startup_gas_p90_deficit'] if b['startup_gas_p90_deficit'] else None)
 result['canonical_MAE_ratios']={h:[y/x if x else None for x,y in zip(baseline['canonical'][h]['model_MAE'],metrics['canonical'][h]['model_MAE'])] for h in ['1','4','8','16','45']}
 return result
for arm in plan['arms']:
 rows=[]
 for epoch in range(10,601,10):
  row=load(O/f'{arm}-epoch{epoch:03}.json');m=row['metrics'];c=checks(baseline,m,plan['acceptance'],scales);rows.append(dict(epoch=epoch,accepted=all(c.values()),guarded=guarded(baseline,m,plan['acceptance'],scales),failed_checks=[k for k,v in c.items() if not v],checks=c,**summary(m)))
 selected=load(O/(arm+'-selection.json'));s=next(r for r in rows if r['epoch']==selected['epoch']) if selected['epoch']>0 else None
 best=min(rows,key=lambda r:max(1-x for x in r['display']['state_MAE_relative_reduction']))
 startup=max(rows,key=lambda r:min(r[x]['startup_p90_relative_reduction'] for x in ['display','autonomous']))
 arms[arm]=dict(selected_epoch=selected['epoch'],selected_accepted=selected['accepted_on_selection'],selected_diagnostics=s,epochs_accepted=sum(r['accepted'] for r in rows),epochs_guarded=sum(r['guarded'] for r in rows),epochs_meeting_each_gate={k:sum(r['checks'][k] for r in rows) for k in rows[0]['checks']},best_worst_display_state_posthoc=best,best_joint_startup_posthoc=startup,rows=rows)
out=dict(selection_diagnosis_only=True,optimizer_updates=0,test_evaluated=False,new_model_selected=False,winner=load(O/'selection-freeze.json')['winner'],arms=arms,scope='Posthoc reading of already frozen development selection trajectories, not a new accepted model or pristine validation. Individual best metrics cannot be combined from different checkpoints. Canonical ratios cover every valid stride1 origin; original acceptance thresholds unchanged. Confirmation is kept separate and cannot switch a checkpoint.')
(R/'results/canonical-pilot03-trajectory-audit.json').write_text(json.dumps(out,indent=2)+'\n')
for arm,a in arms.items():
 print(arm,'selected',a['selected_epoch'],'accepted_epochs',a['epochs_accepted'],'guarded_epochs',a['epochs_guarded'])
 print('selected diagnostics',json.dumps(a['selected_diagnostics']))
 print('gate counts',a['epochs_meeting_each_gate'])
 print('best joint startup',a['best_joint_startup_posthoc']['epoch'],a['best_joint_startup_posthoc']['display'],a['best_joint_startup_posthoc']['autonomous'])
