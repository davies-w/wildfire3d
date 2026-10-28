"""Reserve the full workflow exposure when infrastructure can replace VMs before task start."""
from pathlib import Path
import datetime,fcntl,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,gc,read,save
execution=read('results/timing-decoder-pilot06-execution.json')['name'];x=execution.split('/');live=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert live['state']=='ACTIVE'
text=(R/'data/timing-decoder-pilot06/workflow.yaml').read_text();assert '${sys.now() + 2700}' in text and 'taskCount: \'1\'' in text and 'maxRetryCount: 0' in text
quotas={q['metric']:q for q in gc('compute','project-info','describe')['quotas']};assert quotas['GPUS_ALL_REGIONS']['limit']==1
# At most one billable standard GPU concurrently. Include the entire workflow,
# not a per-VM timer which can reset on an infrastructure replacement.
allowance=(2700+300)*1.2/3600;assert allowance==1.0
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations']['density36-timing-decoder-pilot06'];assert r['execution']==execution and r['state']=='submitted' and r['allowance_usd'] in [.45,1.0]
 updated_reserved=b['reserved_usd']-r['allowance_usd']+allowance;assert b['estimated_spend_usd']+updated_reserved<=b['authorized_usd']==125
 r.setdefault('original_single_vm_allowance_usd',.45);r['allowance_usd']=allowance;r['operational_allowance_amendment']={'reason':'Original0.45 bound covered one VM, not infrastructure replacements before task execution. Reserve whole2700s workflow plus300s cleanup at conservative1.20USD/hour. Task retry count remains0; no new task/VM/job submitted.','maximum_concurrent_standard_gpus':1,'full_workflow_allowance_usd':allowance};b['reserved_usd']=updated_reserved;B.write_text(json.dumps(b,indent=2)+'\n')
proof=dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution=live,original_single_vm_allowance_usd=.45,amended_workflow_allowance_usd=allowance,whole_workflow_s=2700,cleanup_margin_s=300,conservative_rate_usd_per_hour=1.2,maximum_concurrent_standard_gpus=1,estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],remaining_unallocated_usd=125-b['estimated_spend_usd']-b['reserved_usd'],cloud_configuration_changed=False,new_compute_submitted=False,scope='Conservative reservation correction, not actual spend. Immutable original package retains its historical0.45 assumption; this operational ledger amendment supersedes that financial estimate. Model, training, task/workflow deadlines and scientific checks unchanged. Shared charges remain project-level; billing estimates are not final invoices.')
save('results/timing-decoder-pilot06-infrastructure-allowance.json',proof);print(json.dumps({k:v for k,v in proof.items() if k!='execution'},indent=2))
