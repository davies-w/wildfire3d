"""Release four measured, closed original attempts; retain their recovery history."""
from pathlib import Path
import datetime,fcntl,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,BUCKET,gc,read,save
KEYS=['x36-density-032','x36-density-088','x36-density-093','x36-density-115'];empty={'instances':[],'disks':[],'jobs':[]};b=json.loads(B.read_text());assert b['recycle_reservations'];assert read('results/dataset-completeness.json')['passed'];closure=read('results/cloud-campaign-closed.json');assert closure['exact_campaign_grant_absent'] and closure['raw_and_checkpoints_preserved']
executions=gc('workflows','executions','list','fds-density36-parent','--location=us-central1','--limit=1000');assert executions and len(executions)<1000 and all(x['state']!='ACTIVE' for x in executions)
policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET);assert not any(x.get('condition')==closure['exact_condition'] and x['role']=='roles/storage.objectViewer' for x in policy['bindings'])
labels=set(KEYS)|{k+'-r1' for k in KEYS};inventory={k:[x for x in gc(*args) if x.get('labels',{}).get('trial_id') in labels] for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inventory.values())
expected={x['id']:x['cases'] for x in read('active-groups.json')};rows=[]
for key in KEYS:
 recovery=read('data/recovery-collected/'+key+'-r1/verified.json');assert recovery['cleanup_verified'] and recovery['all_full_horizon'];assert read('data/recovery-collected/'+key+'-r1/cleanup.json')==empty
 if key.endswith('032'):
  original=read('data/interrupted/'+key+'/job-status.json');assert original['status']['state']=='FAILED';assert read('data/interrupted/'+key+'/cleanup.json')==empty;complete=[p.stem for p in (R/'data/interrupted'/key).glob('x36_*_s0.json')]
 else:
  original=read('results/preemption-'+key[-3:]+'.json');assert original['cleanup_verified'] and original['cleanup']==empty and original['reason'].startswith('Spot preemption');complete=original['complete_cases'];assert set(original['remaining_cases'])==set(recovery['cases'])
 assert not set(complete)&set(recovery['cases']) and set(complete)|set(recovery['cases'])==set(expected[key]);cost=b['reservations'][key]['cost'];assert cost['stage'] in ['runtime_estimate','posted_billing_subject_to_adjustment'] and cost['usd']>0
 rows.append(dict(key=key,cost_already_in_project_estimate=cost,original_completed_cases=complete,recovered_cases=recovery['cases'],original_and_recovery_closed=True))
if all(b['reservations'][key]['state']=='completed_reconciled' for key in KEYS):
 prior=read('results/closed-preempted-cpu-reconciliation.json');assert prior['phase']=='completed_reconciled';print('Already financially closed; historical proof retained; no budget mutation');raise SystemExit(0)
proof=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase='verified_not_released',rows=rows,live_inventory=inventory,parent_executions=[{k:x.get(k) for k in ['name','state','startTime','endTime']} for x in executions],exact_shared_read_grant_absent=True,dataset_complete=True,flex_storage_transfer_build_orchestration_unchanged=True,no_cost_added_again=True,scope='Financial closure of preempted original attempts whose unfinished cases were separately recovered. Original scientific attempts remain preempted, not relabeled successful. Positive measured/posted original costs are already in the project estimate. No files deleted, jobs changed, or allowances for future work reused implicitly.')
save('results/closed-preempted-cpu-reconciliation.json',proof)
with (B.parent/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());before=b['reserved_usd'];released=[]
 for row in rows:
  key=row['key'];r=b['reservations'][key];assert r['cost']==row['cost_already_in_project_estimate'];assert r['state'] in ['delegated_to_cloud_queue','submitted','completed_reconciled']
  if r['state']!='completed_reconciled':released.append(key);r.update(state='completed_reconciled',historical_allowance_usd=r['allowance_usd'],terminal_evidence='experiments/36_tree_density/results/closed-preempted-cpu-reconciliation.json',terminal_disposition='original_preempted_remaining_cases_recovered_separately')
 b['reserved_usd']=sum(r['allowance_usd'] for r in b['reservations'].values() if r['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd'];B.write_text(json.dumps(b,indent=2)+'\n')
proof.update(phase='completed_reconciled',released_keys=released,released_allowance_usd=before-b['reserved_usd'],estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],headroom_usd=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd']);save('results/closed-preempted-cpu-reconciliation.json',proof);print(json.dumps({k:v for k,v in proof.items() if k not in ['rows','parent_executions']},indent=2))
