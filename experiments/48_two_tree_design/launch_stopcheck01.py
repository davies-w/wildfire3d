"""Single guarded checkpoint diagnostic; carve allowance from existing pilot reserve."""
from cloud48_05 import *
import yaml,datetime,base64
Q=R/'private-stopcheck01';WFTEST='fds-tree48-stopcheck01';assert not (Q/'submission-intent.json').exists()
pkg=json.loads((Q/'package.json').read_text());assert pkg['input_sha256']==sha(R/'data/stopcheck01/input.xz');assert pkg['workflow_sha256']==sha(R/'stopcheck01.yaml')
assert not gc('workflows','executions','list',WFTEST,'--location=us-central1') if (Q/'deployed.json').exists() else True
condition=dict(title='tree48-stopcheck01-read',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/tree48/stopcheck01/') && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
if not (Q/'read-condition.json').exists():(Q/'read-condition.json').write_text(json.dumps(condition))
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(Q/'read-condition.json'))
if not (Q/'input-upload.json').exists():
 gc('storage','cp',str(R/'data/stopcheck01/input.xz'),'gs://'+BUCKET+'/tree48/stopcheck01/input.xz','--if-generation-match=0');meta=gc('storage','objects','describe','gs://'+BUCKET+'/tree48/stopcheck01/input.xz');assert meta['md5_hash']==base64.b64encode(hashlib.md5((R/'data/stopcheck01/input.xz').read_bytes()).digest()).decode();(Q/'input-upload.json').write_text(json.dumps(meta))
sa=gc('workflows','describe',WF,'--location=us-central1')['serviceAccount'];gc('workflows','deploy',WFTEST,'--location=us-central1','--source='+str(R/'stopcheck01.yaml'),'--service-account='+sa)
a=gc('workflows','describe',WFTEST,'--location=us-central1');assert yaml.safe_load(a['sourceContents'])==yaml.safe_load((R/'stopcheck01.yaml').read_text());(Q/'deployed.json').write_text(json.dumps(a))
assert not gc('workflows','executions','list',WFTEST,'--location=us-central1')
assert not gc('batch','jobs','list','--location=us-central1','--filter=name~fds-tree48-stopcheck01')
q={x['metric']:x['limit']-x['usage'] for x in gc('compute','regions','describe','us-central1')['quotas']};assert q['PREEMPTIBLE_CPUS']>=4 and q['IN_USE_ADDRESSES']>=1 and q['SSD_TOTAL_GB']>=30
proof=json.loads((Q/'preservation.json').read_text());assert proof['passed']
with (B.parent/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd'];assert WFTEST not in b['reservations'];assert b['reservations'][WF]['allowance_usd']>1
 b['reservations'][WF]['allowance_usd']-=.75;b['reservations'][WFTEST]=dict(state='submission_pending',allowance_usd=.75,scope='Carved from pilot05 original allowance; one cloud stop/resume acceptance test',reserved_unix=time.time());B.write_text(json.dumps(b,indent=2)+'\n')
 (Q/'submission-intent.json').write_text(json.dumps(dict(time=time.time(),workflow=WFTEST)))
 e=gc('workflows','execute',WFTEST,'--location=us-central1');(Q/'execution.json').write_text(json.dumps(e,indent=2));b['reservations'][WFTEST].update(state='submitted',execution=e['name']);B.write_text(json.dumps(b,indent=2)+'\n');print('SUBMITTED',e['name'])
