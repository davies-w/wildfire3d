"""Frozen four-state metrics pooled by configuration; no fitting or selection."""
from pathlib import Path
import hashlib,json,numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-training-collected.json').read_text())['passed']
 root=R/'data/model-training-results';a=np.load(R/'data/learning/sequences.npz');truth=a['state'];labels=a['activity_labels'];configs=a['configuration'];times=a['time']
 report=json.loads((root/'report.json').read_text());assert len(report['tests'])==10
 out={'features':['water_kg','dry_fuel_kg','fuel_gas_release_kg_s','surface_heating_index_K'],'headline_nominal_seconds':16,'horizons':{},'training':[]}
 for fold in report['folds']:
  out['training'].append({k:fold[k] for k in ['fold','rotation','epochs','selected_epoch','stop_reason']})
 for h in [1,4,8,16,45]:
  rows={p:[] for p in ['all','active','quiet','weak','transition']};counts={p:{'histories':0,'forecast_origins':0} for p in rows};seen=[];durations=[];invalid=0
  for test in report['tests']:
   v=np.load(root/f"fold{test['fold']:02}-horizon{h:02}-predictions.npz");ids=v['case_indices'];pred=v['predicted_physical'];target=truth[ids,h:];base=truth[ids,:91-h]
   assert pred.shape==target.shape and len(set(ids.tolist()))==len(ids)
   seen.extend(ids.tolist());durations.extend((times[ids,h:]-times[ids,:91-h]).ravel().tolist());invalid+=int((~np.isfinite(pred)).sum())
   window=np.lib.stride_tricks.sliding_window_view(labels[ids],h,axis=1);ac=np.isin(window,[1,2]).all(-1);qu=(window==0).all(-1);we=(window==3).all(-1)
   masks={'all':np.ones_like(ac),'active':ac,'quiet':qu,'weak':we,'transition':~(ac|qu|we)}
   for phase,mask in masks.items():
    n=mask.sum(1);keep=n>0;counts[phase]['histories']+=int(keep.sum());counts[phase]['forecast_origins']+=int(mask.sum())
    vals=[np.where(mask[:,:,None],x,0).sum(1)[keep]/n[keep,None] for x in [abs(pred-target),abs(base-target),abs(target)]]
    for c in np.unique(configs[ids[keep]]):rows[phase].append([x[configs[ids[keep]]==c].mean(0) for x in vals])
  assert sorted(seen)==list(range(2080)),h
  result={'steps':h,'nominal_seconds':2*h,'actual_duration_seconds':{'min':min(durations),'max':max(durations),'mean':float(np.mean(durations))},'nonfinite_prediction_elements':invalid,'phases':{}}
  for phase,rr in rows.items():
   info=dict(counts[phase],configurations=len(rr))
   if not rr:info.update(defined=False,reason='No eligible forecast origins')
   else:
    values=np.asarray(rr);means=values.mean(0);finite=bool(np.isfinite(means).all());info.update(defined=finite)
    if finite:
     m,b,t=means;info.update(MAE=m.tolist(),no_change_MAE=b.tolist(),mean_absolute_simulation=t.tolist(),error_vs_simulation_percent=[100*x/y if y else None for x,y in zip(m,t)],improvement_vs_no_change_percent=[100*(1-x/y) if y else None for x,y in zip(m,b)])
    else:info['reason']='Nonfinite predictions retained as invalid; no finite-only filtering'
   result['phases'][phase]=info
  out['horizons'][str(2*h)]=result
 out['scope']='Frozen ScorecardV1 masks; average eligible origins per history, then seed replicas within configuration, then equal weight per eligible configuration across ten disjoint test folds. Percentages are ratios of pooled grouped means, not averages of fold percentages. Zero denominators are undefined. No state clamps. Previously examined reshuffled simulations, not pristine or physical validation. Generic3m cones4/6/8/10m above2m,1600weightedparticles,0.5m grid,1500C20s imposed arc,180s; no trunks/buildings/embers. Gas is kg/s, not heat; heating index is K, not energy.'
 out['report_sha256']=hashlib.sha256((root/'report.json').read_bytes()).hexdigest()
 (R/'results/model-four-state-summary.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 print('Saved pooled four-state scorecard; no fitting or selection performed')
if __name__=='__main__':main()
