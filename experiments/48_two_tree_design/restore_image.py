from cloud48 import *
import datetime
assert not (P/'build.json').exists()
source=PREFIX+'build-source.tgz';bucket=BUCKET
gc('storage','cp','gs://'+PROJECT+'_cloudbuild/source/1793663177.51057-3401629354194e7e8aa1352e5fef6c88.tgz','gs://'+bucket+'/'+source,'--if-generation-match=0')
assert not any(x['status'] in ['WORKING','QUEUED'] for x in gc('builds','list','--limit=10'))
condition=dict(title='tree48-build-source',expression="resource.name == 'projects/_/buckets/"+bucket+"/objects/"+source+"' && request.time < timestamp('"+(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')+"')")
save('build-source-condition.json',condition)
gc('storage','buckets','add-iam-policy-binding','gs://'+bucket,'--member=serviceAccount:fds-builder@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/'build-source-condition.json'))
save('build-repair-intent.json',dict(source=source,time=time.time(),original_rejected_before_build_creation=True))
v=gc('builds','submit','gs://'+bucket+'/'+source,'--config='+str(R/'cloudbuild.yaml'),'--async');save('build.json',v);print(v['id'])
