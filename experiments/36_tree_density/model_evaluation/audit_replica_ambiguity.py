"""TRAIN-only descriptive seed variability; no physical error-floor claim."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 root=R/'data/pair-sequence/rotation0';a=np.load(root/'data/sequences.npz');m=json.loads((root/'schema.json').read_text());ids=np.array(m['rotations'][0]['train']);config=a['configuration'];rows=[];grid=np.arange(0,181,2)
 for c in np.unique(config[ids]):
  group=ids[config[ids]==c]
  if len(group)<2:continue
  gas=np.array([np.interp(grid,a['time'][i],a['state'][i,:,2]) for i in group]);peak=gas.max(1);avg=gas.mean(0);deficit=np.maximum(gas[:,:17]-avg[None,:17],0).max(1)/np.maximum(peak,1e-30);loo=(gas.sum(0)[None]-gas)/(len(group)-1)
  rows.append(dict(configuration=int(c),cases=[m['cases'][int(i)]['case'] for i in group],replicas=len(group),input_geometry_max_range=np.ptp(a['geometry'][group],axis=0).tolist(),initial_state_max_range=np.ptp(a['state'][group,0],axis=0).tolist(),gas_peak_min_max= [float(peak.min()),float(peak.max())],gas_peak_time_range_s=float(np.ptp(grid[gas.argmax(1)])),seed_mean_startup_deficits=deficit.tolist(),leave_one_seed_out_startup_deficits=(np.maximum(gas[:,:17]-loo[:,:17],0).max(1)/np.maximum(peak,1e-30)).tolist(),max_timing_jitter_s=float(np.abs(a['time'][group]-grid).max())))
 out=dict(train_only=True,replicated_configurations=len(rows),histories=sum(r['replicas'] for r in rows),scope='Descriptive seed sensitivity only. Interpolate each retained approximately2s trajectory onto a common nominal2s grid to compare replicas; timing jitter recorded. Seed-mean uses all replicas and is an optimistic oracle, not an independent forecast or a proved irreducible error floor. Leave-one-seed-out uses other TRAIN replicas only. No validation/test outcomes or fitting.',cases=rows)
 if rows:out['summary']=dict(median_seed_mean_startup_deficit=float(np.median([x for r in rows for x in r['seed_mean_startup_deficits']])),median_leave_one_seed_out_startup_deficit=float(np.median([x for r in rows for x in r['leave_one_seed_out_startup_deficits']])),p90_leave_one_seed_out_startup_deficit=float(np.quantile([x for r in rows for x in r['leave_one_seed_out_startup_deficits']],.9)),median_peak_time_range_s=float(np.median([r['gas_peak_time_range_s'] for r in rows])))
 (R/'results/replica-ambiguity-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
