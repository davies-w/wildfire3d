from pathlib import Path
import json,math
import numpy as np
R=Path(__file__).parent
old=list((R.parent/'31_tree_variations/data/cloud').glob('*/result.json'));times=[]
for p in old:
 d=json.loads(p.read_text());times.append(d.get('wall_s',d.get('wall_seconds',0)))
# Measured per-case runtimes are retained verbatim in the source result records.
raw=[json.loads(p.read_text()) for p in old]
actual=[float(d['wall_seconds']) for d in raw if 'wall_seconds' in d]
if not actual:
 print('Available runtime keys',list(raw[0]));raise SystemExit(1)
n=472;groups=math.ceil(n/12);mean=float(np.mean(actual));cpu_proxy=n*(mean+60)/3600*.08
plan=dict(status='estimate_only_not_authorized_or_launched',new_runs=n,cpu_groups=groups,max_concurrent_cpu_VMs=6,vcpus_per_VM=4,cases_per_group_max=12,per_case_solver_timeout_s=1200,group_VM_lifetime_cap_s=16200,group_absolute_deadline_s=18000,CPU_full_reservation_usd=groups*.4,GPU_full_reservation_usd=3,storage_and_ancillary_allowance_usd=4,unallocated_margin_usd=2,proposed_campaign_cap_usd=25,expected_total_usd_range=[5,9],expected_elapsed_hours_range=[10,14],prior_completed_cases=len(actual),prior_mean_solver_wall_s=mean,prior_min_max_solver_wall_s=[min(actual),max(actual)],cpu_estimate_at_conservative_rate_usd=cpu_proxy,rate_assumptions={'CPU_4vCPU_VM_usd_hour':.08,'GPU_whole_VM_usd_hour':.8},timing_method='Observed solver time +60s/case for preprocessing/upload, six parallel workers, batch startup/queue overhead and GPU fitting. Different heights/moisture may change runtime; ETA is not a guarantee.',storage='Keep full raw evidence and training fields in the same cloud region; fetch only selected visualizations locally. Expected tens of GB, roughly40-60GB compressed raw plus50GB decoded fields. Retention beyond this campaign is ongoing storage cost.',safety='Reserve complete group/GPU allowance centrally before submission; no automatic retries or reservation recycling. Cloud deadlines and cleanup. Preserve periodic FDS restart and GPU optimizer checkpoints. Verify same-Linux resume before each long solve. Stop dispatch if cap or deadline would be exceeded.',pricing='Budget assumptions derived from prior experiment planning, not a live invoice or quoted SKU price.')
(R/'results/cost-plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan,indent=2))
if __name__=='__main__':pass
