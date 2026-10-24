"""Replace terminal-job allowances with resource-lifetime cost estimates, preserving history.
Posted project costs are a comparison, not an additional charge on top of the runtime total.
Per-resource posted billing can supersede these estimates once the new export is populated.
"""
from pathlib import Path
import datetime,json,subprocess,fcntl,sys
R=Path(__file__).resolve().parents[1];D=R/'docs/billing-audit-2026-10-23';B=R/'experiments/33_representation_loss/budget.json'
G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud')
rates={('g2-standard-4','STANDARD'):.706832276,('g2-standard-4','SPOT'):(1.14/3.41+4*.21/13.81+16*.10/55.26),('c3-standard-4','SPOT'):(4*5.45/410.6+16*2.48/1642.51)}
def reconcile():
 query='resource.type="gce_instance" AND (protoPayload.methodName="v1.compute.instances.insert" OR protoPayload.methodName="v1.compute.instances.delete") AND timestamp>="2026-10-15T00:00:00Z"'
 events=json.loads(subprocess.check_output([G,'logging','read',query,'--project=tmrw-wildfire-20261015','--limit=5000','--format=json(timestamp,protoPayload.methodName,protoPayload.resourceName,protoPayload.request.machineType,protoPayload.request.scheduling,protoPayload.request.labels,protoPayload.status,operation)'],text=True));assert len(events)<5000,'Inventory may be truncated'
 groups={}
 for e in events:groups.setdefault(e['protoPayload']['resourceName'],[]).append(e)
 records=[]
 def stamp(e):return datetime.datetime.fromisoformat(e['timestamp'].replace('Z','+00:00'))
 for name,es in groups.items():
  inserts=[e for e in es if e['protoPayload']['methodName'].endswith('.insert') and e.get('operation',{}).get('last') and not e['protoPayload'].get('status',{}).get('code')]
  for endinsert in inserts:
   ins=[e for e in es if e.get('operation',{}).get('id')==endinsert['operation']['id'] and e['protoPayload'].get('request',{}).get('machineType')]
   if not ins:continue
   req=ins[0]['protoPayload']['request'];machine=req['machineType'].split('/')[-1];provision=req.get('scheduling',{}).get('provisioningModel','STANDARD');key=(machine,provision)
   dels=[e for e in es if e['protoPayload']['methodName'].endswith('.delete') and e.get('operation',{}).get('last') and not e['protoPayload'].get('status',{}).get('code') and stamp(e)>=stamp(endinsert)]
   if not dels:continue
   deletion=min(dels,key=stamp);starts=[e for e in es if e.get('operation',{}).get('id')==deletion['operation']['id']];end=min(starts,key=stamp);hours=(stamp(end)-stamp(endinsert)).total_seconds()/3600
   assert hours>=0 and key in rates,(name,key,hours)
   labels=req.get('labels',{})
   if isinstance(labels,list):labels={x['key']:x.get('value') for x in labels}
   records.append(dict(vm=name.split('/')[-1],trial_id=labels.get('trial_id'),machine=machine,provisioning=provision,hours=hours,start=endinsert['timestamp'],end=end['timestamp'],estimated_compute_usd=hours*rates[key]))
 assert records
 D.mkdir(exist_ok=True);(D/'vm-runtime.json').write_text(json.dumps(records,indent=2)+'\n')
 # Export has not yet backfilled; these are the independently observed project report totals.
 posted=16.55;shared=1.26;compute=sum(r['estimated_compute_usd'] for r in records)
 export=json.loads(subprocess.check_output([sys.executable,str(R/'scripts/read_billing_export.py'),'--end',(datetime.datetime.now(datetime.timezone.utc).date()+datetime.timedelta(days=1)).isoformat()],text=True))
 billed=export.get('costs') or []
 if billed:posted=sum(float(r['net_cost']) for r in billed)

 result=dict(billing_export_status=export['status'],posted_source='BigQuery detailed export' if billed else 'Previously captured Billing Reports; Oct1–23;16.55USD',as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='runtime_estimate_pending_per_resource_billing',project_posted_comparison_usd=posted,project_compute_runtime_estimate_usd=compute,shared_cost_estimate_usd=shared,spend_estimate_usd=max(posted,compute+shared),matched_vms=len(records),scope='Entire wildfire project since Oct15, including experiments predating32; conservative broader scope than campaign',limitations='VM successful-insert completion to delete request is approximate allocation time; preemption/startup accounting differs. Spot rates estimated from rounded posted SKU amounts. Shared costs use currently posted disk/IP/workflow totals. Not invoice or per-job actual charges. Compare totals using max, never add posted and runtime totals.',rates_usd_per_vm_hour={'/'.join(k):v for k,v in rates.items()})
 with (B.parent/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());b.setdefault('historical_allowances_usd',b['reserved_usd']);b['accounting_policy']='Expected estimate -> measured-runtime cost estimate -> posted charge, preserving history. Historical maximum allowances are not spend. Supersedes retained-allowance accounting by explicit user instruction.';b['recycle_reservations']=True;b['accounting']=result
  for key,res in b['reservations'].items():
   workflow=res.get('execution','').split('/workflows/')[-1].split('/executions/')[0]
   match=[r for r in records if workflow and (r.get('trial_id')==workflow.removeprefix('fds-') or r['vm'].startswith(workflow+'-'))]
   if match:res['cost']=dict(stage='runtime_estimate',usd=sum(r['estimated_compute_usd'] for r in match),vm_hours=sum(r['hours'] for r in match),scope='compute only; shared cost at project level',resources=[r['vm'] for r in match]);res['historical_allowance_usd']=res['allowance_usd']
   if match and billed:
    # Only replace when identifiable resource records cover each allocation's whole interval
    # and contain all compute resource categories. Otherwise retain the runtime estimate.
    actual=[row for row in billed if any(r['vm'] in (row.get('resource_name') or '') for r in match)]
    covered=bool(actual)
    def ts(x):return datetime.datetime.fromisoformat(x.replace(' UTC','+00:00').replace('Z','+00:00'))
    for vm in match:
     rows=[r for r in actual if vm['vm'] in (r.get('resource_name') or '') and r['service']=='Compute Engine']
     kinds=['Core','Ram']+(['GPU'] if vm['machine'].startswith('g2') else [])
     for kind in kinds:
      rr=[r for r in rows if kind.lower() in r['sku'].lower()]
      covered=covered and bool(rr) and min(ts(r['first_usage_start']) for r in rr)<=ts(vm['start']) and max(ts(r['last_usage_end']) for r in rr)>=ts(vm['end'])
    if covered:res['cost']=dict(stage='posted_billing_subject_to_adjustment',usd=sum(float(r['net_cost']) for r in actual),scope='matched detailed-export resource rows; shared/unattributed costs separate',resource_rows=len(actual))

  active=[r for r in b['reservations'].values() if r['state'] in ['reserved_before_upload','submission_pending','submitted']]
  b['reserved_usd']=sum(r['allowance_usd'] for r in active);b['estimated_spend_usd']=result['spend_estimate_usd'];B.write_text(json.dumps(b,indent=2)+'\n')
 (D/'runtime-reconciliation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':reconcile()
