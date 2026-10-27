"""Release pilot01 compute allowance only with terminal cleanup and failed inserts proof."""
import sys,json,fcntl,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,gc,read,save
KEY='density36-exposure-pilot01'
def main():
 assert read('results/exposure-pilot-incomplete.json')['cleanup_verified'];assert read('results/exposure-pilot-status.json')['state']!='ACTIVE';assert read('results/exposure-pilot-permission-removed.json')['exact_grant_removed']
 for cmd in [('batch','jobs','list','--location=us-central1'),('compute','instances','list'),('compute','disks','list')]:
  items=gc(*cmd);assert not any(x['name'].rsplit('/',1)[-1].startswith('fds-gpu36-exposure') for x in items)
 ops=gc('compute','operations','list','--filter=targetLink~fds-gpu36-exposure');inserts=[x for x in ops if x.get('operationType')=='insert' and '/instances/' in x.get('targetLink','')];assert inserts,'No authoritative allocation attempts found'
 assert all(x.get('status')=='DONE' and x.get('error',{}).get('errors') for x in inserts),'Successful or unresolved VM allocation; must reconcile measured runtime instead'
 for x in inserts:assert all(e['code'] in ['ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS','ZONE_RESOURCE_POOL_EXHAUSTED'] for e in x['error']['errors'])
 job=read('data/exposure-pilot01-results/job-status.json');assert job['status'].get('runDuration','0s')=='0s';assert job['status']['taskGroups']['group0']['counts'].get('PENDING')=='1'
 proof=dict(passed=True,compute_allocation_seconds=0,successful_vm_inserts=0,failed_capacity_inserts=len(inserts),task_run_duration='0s',basis='Every retained VM insert operation completed with capacity error; zero task runtime; live job/VM/disk prefix inventory empty; exact temporary read permission removed.',not_a_posted_bill=True,ancillary_costs='Workflow/storage remain covered by existing ancillary reservations; no zero-total-project-cost claim.',operations=inserts)
 save('results/exposure-pilot-zero-allocation-proof.json',proof)
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());entry=b['reservations'][KEY]
  if entry['state']=='terminal_no_compute_allocation':assert entry['allowance_usd']==0;return
  assert entry['state']=='submitted' and entry['allowance_usd']==.75;entry.update(state='terminal_no_compute_allocation',historical_allowance_usd=.75,allowance_usd=0,compute_cost_estimate_usd=0,reconciled_unix=time.time(),cost_basis='Verified zero successful GPU VM allocations; ancillary costs covered separately');b['reserved_usd']=round(b['reserved_usd']-.75,8);B.write_text(json.dumps(b,indent=2)+'\n')
 save('results/exposure-pilot-budget-released.json',dict(released_compute_allowance_usd=.75,estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],cap_usd=b['authorized_usd'],zero_allocation_proof='results/exposure-pilot-zero-allocation-proof.json'));print('Verified no GPU compute allocated; released0.75USD compute allowance; ancillary reservations retained')
if __name__=='__main__':main()
