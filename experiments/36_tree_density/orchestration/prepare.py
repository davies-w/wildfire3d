"""Freeze cloud-only queue and generate durable bounded parent workflow."""
from pathlib import Path
import json,hashlib,yaml,datetime,fcntl,time
R=Path(__file__).resolve().parent.parent; O=R/'orchestration';B=R.parent/'33_representation_loss/budget.json'
P='tmrw-wildfire-20261015';bucket=P+'-trial';base='https://workflowexecutions.googleapis.com/v1/projects/'+P+'/locations/us-central1/workflows/'
with (R/'data/dispatcher.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 gs=json.loads((R/'active-groups.json').read_text());todo=[g for g in gs if not (R/'jobs'/g['id']/'execution.json').exists()]
 assert len(todo)==102
 for g in todo:
  assert hashlib.sha256((R/g.get('package_file','data/packages/'+g['id']+'.xz')).read_bytes()).hexdigest()==g['package_sha256']
  assert hashlib.sha256((R/'jobs'/g['id']/g['workflow_file']).read_bytes()).hexdigest()==g['workflow_sha256']
 (O/'queue.json').write_text(json.dumps(todo,indent=2)+'\n')
 with (B.parent/'data/budget.lock').open('w') as bl:
  fcntl.flock(bl,fcntl.LOCK_EX);b=json.loads(B.read_text())
  if 'density36-cloud-orchestration' not in b['reservations']:
   assert b['estimated_spend_usd']+b['reserved_usd']+1<=125
   b['reservations']['density36-cloud-orchestration']=dict(state='reserved_before_upload',allowance_usd=1,reserved_unix=time.time(),scope='Bounded cloud workflow orchestration; user authorized sleep-independent execution')
   b['reserved_usd']=round(b['reserved_usd']+1,2);B.write_text(json.dumps(b,indent=2)+'\n')
expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%SZ')
condition=dict(title='density36-cloud-queue-read',description='Time-limited private campaign inputs and result verification',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+bucket+"/objects/density36/')")
(O/'read-condition.json').write_text(json.dumps(condition,indent=2)+'\n')
auth={'type':'OAuth2'}
def get(url,result):return {'try':{'call':'http.get','args':{'url':url,'auth':auth},'result':result},'retry':'${http.default_retry} }
def write(name,body):return {'call':'http.post','args':{'url':'https://storage.googleapis.com/upload/storage/v1/b/'+bucket+'/o','query':{'uploadType':'media','name':name,'ifGenerationMatch':0},'auth':auth,'headers':{'Content-Type':'application/json'},'body':body}}
steps=[{'intent':write('${"density36/orchestration/intents/" + g.id + ".json"}','${g}')},
 {'prior':get('${"'+base+'fds-" + g.id + "/executions"}','prior')},
 {'unique':{'switch':[{'condition':'${len(default(map.get(prior.body,"executions"),[])) != 0}','raise':'Existing execution found; refusing duplicate'}]}},
 {'create':{'call':'http.post','args':{'url':'${"'+base+'fds-" + g.id + "/executions"}','auth':auth,'body':{}},'result':'created'}},
 {'save_execution':write('${"density36/orchestration/executions/" + g.id + ".json"}','${created.body}')},
 {'deadline':{'assign':[{'deadline':'${sys.now()+18000}'}]}},
 {'poll':get('${"https://workflowexecutions.googleapis.com/v1/" + created.body.name}','execution')},
 {'check':{'switch':[{'condition':'${execution.body.state == "SUCCEEDED"}','next':'scientific'},{'condition':'${execution.body.state != "ACTIVE" or sys.now() > deadline}','raise':'Child workflow failed or exceeded bounded deadline'}]}},
 {'wait':{'call':'sys.sleep','args':{'seconds':60},'next':'poll'}},
 {'scientific':{'assign':[{'result':'${json.decode(execution.body.result)}'}]}},
 {'success':{'switch':[{'condition':'${result.final_state != "SUCCEEDED" or result.workers_remaining != 0}','raise':'Batch task did not succeed; cleanup success alone is insufficient'}]}},
 {'summaries':{'for':{'value':'c','in':'${g.cases}','steps':[
  {'summary':get('${"https://storage.googleapis.com/'+bucket+'/density36/" + g.id + "/" + c + ".summary.json"}','summary')},
  {'validate':{'switch':[{'condition':'${not summary.body.result.full_horizon or not summary.body.resume.passed or summary.body.result.binary_sha256 != "70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692" or summary.body.deck_sha256 != g.deck_hashes[c]}','raise':'Scientific summary verification failed'}]}}
 ]}}},
 {'complete':write('${"density36/orchestration/completed/" + g.id + ".json"}',{'group':'${g.id}','cases':'${len(g.cases)}','all_full_horizon':True,'execution':'${created.body.name}'})},
 {'done':{'return':'${g.id}'}}]
freeze=json.loads((R/'results/input-freeze.json').read_text())['cases']
queue=[{'id':g['id'],'cases':g['cases'],'deck_hashes':{c:freeze[c] for c in g['cases']}} for g in todo]
# Queue is loaded from immutable GCS object to remain below workflow source size limits.
(O/'run-queue.json').write_text(json.dumps(queue)+'\n')
w={'main':{'steps':[{'lease':write('density36/orchestration/parent-lease.json',{'execution':'${sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}','purpose':'Single-owner campaign queue'})},{'load':get('https://storage.googleapis.com/'+bucket+'/density36/orchestration/run-queue.json','queue')},{'run':{'parallel':{'concurrency_limit':20,'for':{'value':'g','in':'${queue.body}','steps':[{'group':{'call':'run_group','args':{'g':'${g}'}}}]}}}},{'done':{'return':{'complete':True,'groups':len(todo)}}}]},'run_group':{'params':['g'],'steps':steps}}
(O/'parent.yaml').write_text(yaml.safe_dump(json.loads(json.dumps(w)),sort_keys=False))
(O/'preflight.json').write_text(json.dumps(dict(groups=len(todo),cases=sum(len(g['cases']) for g in todo),concurrency=20,unchanged_packages=True,unchanged_child_workflows=True,no_local_dependency_after_execution=True,create_retries=False,per_group_immutable_intent=True),indent=2)+'\n')
print('Prepared',len(todo),'groups')
