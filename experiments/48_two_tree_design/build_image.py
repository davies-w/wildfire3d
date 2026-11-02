from cloud48 import *
import datetime
assert not (P/'build.json').exists()
assert not any(x['status'] in ['WORKING','QUEUED'] for x in gc('builds','list','--limit=10'))
condition=dict(title='tree48-build-staging',expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+PREFIX+"build/') && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
save('build-staging-condition.json',condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-builder@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'build-staging-condition.json'))
save('build-staging-intent.json',dict(time=time.time()))
v=gc('builds','submit',str(R/'data/cloud-context'),'--gcs-source-staging-dir=gs://'+BUCKET+'/'+PREFIX+'build','--config='+str(R/'cloudbuild.yaml'),'--async');save('build.json',v);print(v['id'])
