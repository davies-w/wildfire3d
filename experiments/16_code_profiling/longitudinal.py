"""Measure actual CPU per physical-time window and CPU-to-label in the long run."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
a=json.loads((ROOT/'results/analysis.json').read_text())
r=next((r for r in a['runs'] if r['case']=='lot_full'),None)
if r is None:raise RuntimeError('Long-run evidence has not arrived')
prefix=r['prefix_cost'];t=np.array([v['simulated_s'] for v in prefix]);cpu=np.array([v['cpu_s'] for v in prefix]);last=float(t[-1])
def at(v):return float(np.interp(v,t,cpu))
windows=[]
for start in range(0,int(last)+1,30):
 end=min(start+30,last)
 if end<=start:continue
 used=at(end)-(at(start) if start else 0)
 windows.append(dict(start_s=start,end_s=end,cpu_s=used,cpu_s_per_simulated_s=used/(end-start),full_30s_window=end-start==30))
result={'last_device_time_s':r['physical_seconds_reached'],'last_step_time_s':last,'requested_s':r['horizon_s'],'full_horizon':r['full_horizon'],'os_total_cpu_s':r['cpu_total_s'],'ignition_label':r['ignition_label'],'first_ignition_event_s':r['first_ignition_event_s'],'estimated_cpu_to_first_ignition_s':r.get('estimated_cpu_to_first_ignition_s'),'cpu_budget_300s_reaches_physical_s':float(np.interp(300,cpu,t)) if cpu[-1]>=300 else None,'windows':windows,'caveat':'CPU-to-event uses interpolation of recorded process CPU. A partial run without ignition has no negative label. Per-window CPU includes solver initialization in the first window; OS totals also include shutdown.'}
(ROOT/'results/longitudinal.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
