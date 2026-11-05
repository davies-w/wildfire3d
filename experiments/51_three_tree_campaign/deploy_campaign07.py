"""Deploy approved unique rolling07 and no-solver readiness; never submit solver."""
from cloud07 import *
import yaml,requests,base64,concurrent.futures,urllib.parse
assert not (P/'submission-intent.json').exists()
pkg=json.loads((P/'package.json').read_text());D=R/'data/cloud07'
for n,h in pkg['files'].items():assert sha(D/n)==h,n
assert json.loads((R/'private04/continuation-authorization.json').read_text())['rolling_fallback_authorized']
expiry=json.loads((R/'private02/permission-approval.json').read_text())['condition']
for who,title,file in [('fds-worker','tree51-campaign07-read','read-condition.json'),('fds-watchdog','tree51-campaign07-controller-read','controller-read-condition.json')]:
 condition=dict(title=title,expression="resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+PREFIX+"') && "+expiry);save(file,condition)
 gc('storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+who+'@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(P/file))
for role,title,file,permissions in [('fdsTree51TaskReader','tree51-task-read07','task-read-condition.json',{'batch.tasks.list'}),('fdsTree51WaveRunner','tree51-campaign07-execution-run','execution-run-condition.json',{'workflows.executions.create','workflows.executions.get'})]:
 assert set(gc('iam','roles','describe',role)['includedPermissions'])==permissions
 save(file,dict(title=title,expression=expiry));gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com','--role=projects/'+PROJECT+'/roles/'+role,'--condition-from-file='+str(P/file))
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();headers={'Authorization':'Bearer '+token};receipts=P/'input-upload-receipts';receipts.mkdir(exist_ok=True)
def upload(pair):
 f,name=pair;data=f.read_bytes();md=base64.b64encode(hashlib.md5(data).digest()).decode();record=receipts/(hashlib.sha256(name.encode()).hexdigest()+'.json');url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(PREFIX+name,safe='')
 if record.exists():
  old=json.loads(record.read_text());assert old['md5Hash']==md;return old
 # Read before immutable create: safe resume of input upload, never retries a job.
 r=requests.get(url,headers=headers,timeout=60)
 if r.status_code==404:
  r=requests.post('https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',params={'uploadType':'media','name':PREFIX+name,'ifGenerationMatch':0},headers=dict(headers,**{'Content-Type':('application/json' if name.endswith('.json') else 'application/octet-stream')}),data=data,timeout=120)
 r.raise_for_status();meta=r.json();assert meta['md5Hash']==md and int(meta['size'])==len(data);record.write_text(json.dumps(meta));return meta
files=[(f,str(f.relative_to(D))) for f in sorted((D/'inputs').rglob('*')) if f.is_file()]+[(P/'controller-admission-v4.json','control/admission-v4.json')]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 records=[]
 for v in pool.map(upload,files):
  records.append(v)
  if len(records)%250==0:print('Verified input objects',len(records),'/',len(files),flush=True)
save('input-uploads.json',records)
for kind in ['case','epoch','parent','check']:
 name=WF+('-'+kind if kind!='parent' else '')
 gc('workflows','deploy',name,'--location=us-central1','--source='+str(R/('rolling07-'+kind+'.yaml')),'--service-account=fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com')
 actual=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==yaml.safe_load((R/('rolling07-'+kind+'.yaml')).read_text());save('deployed-'+kind+'.json',dict(passed=True,revision=actual.get('revisionId'),sha256=sha(R/('rolling07-'+kind+'.yaml'))))
if not (P/'readiness-execution.json').exists():save('readiness-execution.json',gc('workflows','execute',WF+'-check','--location=us-central1'))
print('Deployed and submitted readiness only; NOsimulationlaunch',flush=True)
