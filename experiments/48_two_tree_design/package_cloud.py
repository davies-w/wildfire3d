"""Freeze pilot inputs and generate a two-wave cloud-owned controller; no submission."""
from cloud48 import *
import yaml,lzma,base64,copy,ast
assert not (P/'submission-intent.json').exists()
b=json.loads((P/'build-status.json').read_text());assert b['status']=='SUCCESS'
image=b['results']['images'][0];uri=image['name'].rsplit(':',1)[0]+'@'+image['digest']
D=R/'data/cloud';D.mkdir(exist_ok=True)
cases=json.loads((R/'data/pilot/cases.json').read_text());canaries=[cases[i] for i in [8,9,18,19]];rest=[c for c in cases if c not in canaries];assert len(canaries)==4 and len(rest)==20
payload={'worker.py':(R/'pilot_worker.py').read_text(),'transport.py':(R/'transport.py').read_text(),'groups.json':json.dumps({'canary':canaries,'bulk':rest})}
for c in cases:payload['decks/'+c['pilot_case']+'.fds']=(R/'data/pilot/decks'/(c['pilot_case']+'.fds')).read_text()
blob=lzma.compress(json.dumps(payload).encode());(D/'input.xz').write_bytes(blob);digest=sha(D/'input.xz')
boot="""import os,json,lzma,pathlib,urllib.request,hashlib,sys,runpy
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
tok=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
r=urllib.request.Request('https://storage.googleapis.com/BUCKET/PREFIXinput.xz',headers={'Authorization':'Bearer '+tok})
blob=urllib.request.urlopen(r,timeout=120).read();assert hashlib.sha256(blob).hexdigest()=='DIGEST'
payload=json.loads(lzma.decompress(blob));root=pathlib.Path('/study');root.mkdir(exist_ok=True)
for n,v in payload.items():
 p=root/n;assert p.is_relative_to(root) and '..' not in pathlib.Path(n).parts;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
group=os.environ['PILOT_GROUP'];index=int(os.environ['BATCH_TASK_INDEX']);case=json.loads(payload['groups.json'])[group][index]
(root/'task.json').write_text(json.dumps({'case':case,'output_prefix':'PREFIX'+group+'/'+case['pilot_case']+'/'}))
sys.path.insert(0,str(root));runpy.run_path(str(root/'worker.py'),run_name='__main__')
""".replace('BUCKET',BUCKET).replace('PREFIX',PREFIX).replace('DIGEST',digest)
(D/'bootstrap.py').write_text(boot)
old=yaml.safe_load((R.parent/'46_cone_recurrent10/pool03.yaml').read_text())
inventory=copy.deepcopy(old['inventory']);cleanup=copy.deepcopy(old['cleanup'])
def http(method,url,result=None,**kw):
 d={'call':'http.'+method,'args':{'url':url,'auth':{'type':'OAuth2'},**kw}}
 if result:d['result']=result
 return d
def record(name,body):return http('post','https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',query={'uploadType':'media','name':name},headers={'Content-Type':'application/json'},body=body)
# Boot disks can lack VM labels: inventory by this unique pilot name prefix as well.
def disk_scope(v):
 if isinstance(v,list):
  for x in v:disk_scope(x)
 elif isinstance(v,dict):
  if v.get('call')=='http.get' and '/disks' in str(v.get('args',{}).get('url','')):v['args']['query']={'filter':'name eq fds-tree48-pilot01-.*'}
  for x in v.values():disk_scope(x)
disk_scope(inventory)
cleanup['steps'].insert(5,{'orphan_disks':{'for':{'value':'disk','in':'${left.disks}','steps':[{'unused':{'switch':[{'condition':'${len(default(map.get(disk,"users"),[])) == 0}','steps':[{'delete_disk':{'try':http('delete','${disk.selfLink}'),'retry':'${http.default_retry}'}}]}]}}]}}})
candidates=[]
for group,cs,machine,memory in [('canary',canaries,'c3-standard-4',12000),('bulk',rest,'c3-highmem-4',28000)]:
 label='tree48-pilot01-'+group
 job={'taskGroups':[{'taskCount':str(len(cs)),'parallelism':str(len(cs)),'taskCountPerNode':'1','taskSpec':{'computeResource':{'cpuMilli':4000,'memoryMib':memory},'maxRunDuration':'10800s','maxRetryCount':0,'environment':{'variables':{'PILOT_GROUP':group}},'runnables':[{'container':{'imageUri':uri,'entrypoint':'python3','commands':['-c',boot],'options':f'--cpus=4 --memory={memory}m --pids-limit=256'}}]}}],'allocationPolicy':{'instances':[{'policy':{'machineType':machine,'provisioningModel':'SPOT','bootDisk':{'sizeGb':'30','type':'pd-balanced'}}}],'location':{'allowedLocations':['zones/us-central1-'+z for z in 'abc']},'serviceAccount':{'email':'fds-worker@'+PROJECT+'.iam.gserviceaccount.com'},'labels':{'trial_id':label},'network':{'networkInterfaces':[{'network':'projects/'+PROJECT+'/global/networks/fds-trial','subnetwork':'projects/'+PROJECT+'/regions/us-central1/subnetworks/fds-trial'}]}},'labels':{'trial_id':label},'logsPolicy':{'destination':'CLOUD_LOGGING'}}
 candidates.append(dict(id=group,job_id='fds-'+label,label=label,region='us-central1',zones=['us-central1-'+z for z in 'abc'],job=job))
JOB='${"https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/" + c.region + "/jobs/" + c.job_id}'
steps=[{'quota_gate':{'call':'await_quota','args':{'c':'${c}'}}},{'create':http('post','https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/jobs',query={'jobId':'${c.job_id}'},body='${c.job}')}, {'set_deadline':{'assign':[{'deadline':'${sys.now()+14400}'}]}}, {'get':http('get',JOB,'state')}, {'record_state':record('${"'+PREFIX+'"+c.id+"/job-status.json"}','${state.body}')}, {'terminal':{'switch':[{'condition':'${state.body.status.state == "SUCCEEDED"}','next':'clean_success'},{'condition':'${state.body.status.state == "FAILED"}','raise':'Pilot worker failed; bulk wave is blocked'}]}}, {'inv':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}}, {'check_age':{'for':{'value':'vm','in':'${inv.vms}','steps':[{'limit':{'switch':[{'condition':'${sys.now() > time.parse(vm.creationTimestamp)+11100}','raise':'Worker VM lifetime exceeded'}]}}]}}}, {'controller_limit':{'switch':[{'condition':'${sys.now()>deadline}','raise':'Queue/run deadline exceeded'}]}}, {'wait':{'call':'sys.sleep','args':{'seconds':30},'next':'get'}}, {'clean_success':{'call':'cleanup','args':{'c':'${c}'}}}]
# If a creation response is lost, cleanup still inventories the known IDs and labels.
w={'main':{'steps':[{'init':{'assign':[{'candidates':candidates}]}},{'campaign':{'try':{'steps':[{'waves':{'for':{'value':'c','in':'${candidates}','steps':steps}}}]},'except':{'as':'failure','steps':[{'cleanup_all':{'for':{'value':'c','in':'${candidates}','steps':[{'clean_failed':{'call':'cleanup','args':{'c':'${c}'}}}]}}},{'record_failure':record(PREFIX+'controller-error.json','${failure}')},{'raise_failure':{'raise':'${failure}'}}]}}},{'done':{'return':{'passed':True,'cases':24,'cleanup_verified':True}}}]},'inventory':inventory,'cleanup':cleanup}
def retry(v):
 if isinstance(v,list):return [retry(x) for x in v]
 if not isinstance(v,dict):return v
 if v.get('call') in ['http.get','http.delete']:return {'try':v,'retry':'${http.default_retry}'}
 if 'retry' in v:return v
 return {k:retry(x) for k,x in v.items()}
w['await_quota']={'params':['c'],'steps':[
 {'init':{'assign':[{'deadline':'${sys.now()+21600}'}]}},
 {'canary':{'switch':[{'condition':'${c.id == "canary"}','return':True}]}},
 {'get':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/regions/us-central1','q')},
 {'reset':{'assign':[{'available':0}]}},
 {'quotas':{'for':{'value':'item','in':'${q.body.quotas}','steps':[{'spot':{'switch':[{'condition':'${item.metric == "PREEMPTIBLE_CPUS"}','assign':[{'available':'${item.limit-item.usage}'}]}]}}]}}},
 {'ready':{'switch':[{'condition':'${available >= 80}','return':True},{'condition':'${sys.now()>deadline}','raise':'Spot CPU quota not granted within six hours; no bulk workers launched'}]}},
 {'wait':{'call':'sys.sleep','args':{'seconds':60},'next':'get'}}]}
w=retry(w);(R/'pilot01.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
ready={'main':{'steps':[{'init':{'assign':[{'candidates':candidates}]}},{'check':{'for':{'value':'c','in':'${candidates}','steps':[{'inspect':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}},{'empty':{'switch':[{'condition':'${len(inv.vms)>0 or len(inv.disks)>0}','raise':'Existing pilot resources'}]}}]}}},{'done':{'return':{'passed':True}}}]},'inventory':inventory}
(R/'readiness.yaml').write_text(yaml.safe_dump(ready,sort_keys=False))
for s in [boot,payload['worker.py'],payload['transport.py']]:ast.parse(s)
save('package.json',dict(input_sha256=digest,image_uri=uri,candidates=[{k:v for k,v in c.items() if k!='job'} for c in candidates],workflow_sha256=sha(R/'pilot01.yaml'),cases=24,canary_cases=[c['pilot_case'] for c in canaries],zero_retries=True))
print('Prepared four canaries followed by 20 parallel workers; all four must succeed before bulk.')
