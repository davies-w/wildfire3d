"""Upload exact inputs, grant scoped read access, deploy and exercise read-only readiness."""
from cloud import *
import datetime,base64,yaml
assert not (P/'submission-intent.json').exists()
pkg=json.loads((P/'package.json').read_text());assert sha(R/'data/cloud/input.xz')==pkg['input_sha256']
prefixes=[PREFIX]
expression='('+' || '.join("resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+p+"')" for p in prefixes)+") && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')"
condition=dict(title='tree49-compact01-read',expression=expression)
if not (P/'read-condition.json').exists():save('read-condition.json',condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'read-condition.json'))
if not (P/'input-upload.json').exists():
 gc('storage','cp',str(R/'data/cloud/input.xz'),'gs://'+BUCKET+'/'+PREFIX+'input.xz','--if-generation-match=0')
 meta=gc('storage','objects','describe','gs://'+BUCKET+'/'+PREFIX+'input.xz');assert meta['md5_hash']==base64.b64encode(hashlib.md5((R/'data/cloud/input.xz').read_bytes()).digest()).decode();save('input-upload.json',meta)
sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
for name,file in [(WF,'workflow.yaml'),(WF+'-check','readiness.yaml')]:
 gc('workflows','deploy',name,'--location=us-central1','--source='+str(R/file),'--service-account='+sa)
 actual=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==yaml.safe_load((R/file).read_text())
if not (P/'readiness-execution.json').exists():save('readiness-execution.json',gc('workflows','execute',WF+'-check','--location=us-central1'))
print('Deployed; readiness execution submitted. No simulation jobs launched.')
