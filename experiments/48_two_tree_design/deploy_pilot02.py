"""Upload exact inputs, grant scoped read access, deploy and exercise read-only readiness."""
from cloud48_02 import *
import datetime,base64,yaml
assert not (P/'submission-intent.json').exists()
pkg=json.loads((P/'package.json').read_text());assert sha(R/'data/cloud02/input.xz')==pkg['input_sha256']
condition=dict(title='tree48-pilot02-read',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+PREFIX+"') && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
if not (P/'read-condition.json').exists():save('read-condition.json',condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'read-condition.json'))
if not (P/'input-upload.json').exists():
 gc('storage','cp',str(R/'data/cloud02/input.xz'),'gs://'+BUCKET+'/'+PREFIX+'input.xz','--if-generation-match=0')
 meta=gc('storage','objects','describe','gs://'+BUCKET+'/'+PREFIX+'input.xz');assert meta['md5_hash']==base64.b64encode(hashlib.md5((R/'data/cloud02/input.xz').read_bytes()).digest()).decode();save('input-upload.json',meta)
sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
for name,file in [(WF,'pilot02.yaml'),(WF+'-check','readiness02.yaml')]:
 gc('workflows','deploy',name,'--location=us-central1','--source='+str(R/file),'--service-account='+sa)
 actual=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==yaml.safe_load((R/file).read_text())
if not (P/'readiness-execution.json').exists():save('readiness-execution.json',gc('workflows','execute',WF+'-check','--location=us-central1'))
print('Deployed; readiness execution submitted. No simulation jobs launched.')
