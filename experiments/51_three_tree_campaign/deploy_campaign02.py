"""Deploy frozen bounded workflow and read-only readiness; no simulation submission."""
from cloud02 import *
import datetime,yaml,concurrent.futures,base64
assert not (P/'submission-intent.json').exists()
pkg=json.loads((P/'package.json').read_text());assert sha(R/'workflow02.yaml')==pkg['workflow_sha256']
assert json.loads((P/'reservation.json').read_text())['passed']
assert sha(R/'wave02.yaml')==pkg['wave_sha256']
a=json.loads((P/'authorization.json').read_text())
admission=dict(passed=True,mode='bounded_campaign_may_stop_before2000',compute_limit_usd=a['compute_limit_usd'],rate_usd_per_vm_hour=a['rate_usd_per_vm_hour'],reserve_seconds_per_vm=a['reserve_seconds_per_vm'],manifest_sha256=pkg['manifest_sha256'],workflow_sha256=pkg['workflow_sha256'])
save('controller-admission-v2.json',admission)
condition=dict(title='tree51-campaign02-read',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+PREFIX+"') && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=96)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
if not (P/'read-condition.json').exists():save('read-condition.json',condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'read-condition.json'))
controller_condition=dict(json.loads((P/'read-condition.json').read_text()),title='tree51-campaign02-controller-read')
save('controller-read-condition.json',controller_condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'controller-read-condition.json'))
def put(pair):
 path,name=pair;receipt=P/('upload-'+path.name+'.json')
 if receipt.exists():
  old=json.loads(receipt.read_text());assert old['md5_hash']==base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode(),'Frozen upload bytes changed';return old
 gc('storage','cp',str(path),'gs://'+BUCKET+'/'+PREFIX+name,'--if-generation-match=0')
 meta=gc('storage','objects','describe','gs://'+BUCKET+'/'+PREFIX+name)
 assert meta['md5_hash']==base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode();receipt.write_text(json.dumps(meta,indent=2)+'\n');return meta
files=[(f,'inputs/'+f.name) for f in sorted((R/'data/cloud02').glob('wave-*.xz'))]+[(R/'data/cloud02/manifest.json','inputs/manifest.json'),(P/'controller-admission-v2.json','control/admission-v2.json')]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(put,files))
save('input-uploads.json',results)
sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
for name,file in [(WF+'-wave','wave02.yaml'),(WF,'workflow02.yaml'),(WF+'-check','readiness02.yaml')]:
 gc('workflows','deploy',name,'--location=us-central1','--source='+str(R/file),'--service-account='+sa)
 actual=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==yaml.safe_load((R/file).read_text())
expiry=condition['expression'].split(" && ")[-1]
save('task-read-condition.json',dict(title='tree51-task-read02',expression=expiry))
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/fdsTree51TaskReader','--condition-from-file='+str(P/'task-read-condition.json'))
# Only execution creation/read on this one child workflow, expiring with the campaign.
resource='projects/'+PROJECT+'/locations/us-central1/workflows/'+WF+'-wave'
save('wave-run-condition.json',dict(title='tree51-campaign02-wave-run',expression="resource.name.startsWith('"+resource+"') && "+expiry))
role='fdsTree51WaveRunner'
roles=gc('iam','roles','list','--filter=name:roles/'+role)
if not roles:gc('iam','roles','create',role,'--title=Tree51 child execution create and get','--permissions=workflows.executions.create,workflows.executions.get','--stage=GA')
actual=gc('iam','roles','describe',role);assert set(actual['includedPermissions'])=={'workflows.executions.create','workflows.executions.get'}
gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/'+role,'--condition-from-file='+str(P/'wave-run-condition.json'))
if not (P/'readiness-execution.json').exists():save('readiness-execution.json',gc('workflows','execute',WF+'-check','--location=us-central1'))
print('Deployed frozen workflows; read-only readiness submitted; no simulation jobs launched')
