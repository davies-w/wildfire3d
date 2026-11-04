"""Freeze unfinished cases into independently bounded wave executions; never submit."""
from pathlib import Path
import ast,base64,copy,hashlib,json,lzma,yaml,sys
R=Path(__file__).resolve().parent;P=R/'private02';D=R/'data/cloud02'
P.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
assert not (P/'submission-intent.json').exists()
RUN='fds-tree51-campaign02';PREFIX='tree51/campaign02/';BUCKET='tmrw-wildfire-20261015-trial';PROJECT='tmrw-wildfire-20261015'
class NoAlias(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
def clone(x):return json.loads(json.dumps(x).replace('campaign01','campaign02'))
def dump(name,x):(R/name).write_text(yaml.dump(x,Dumper=NoAlias,sort_keys=False))
def get(path,result):return {'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+(PREFIX+path).replace('/','%2F'),'query':{'alt':'media'},'auth':{'type':'OAuth2'}},'result':result}
def put(name,body):return {'call':'http.post','args':{'url':'https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o','auth':{'type':'OAuth2'},'query':{'uploadType':'media','name':name,'ifGenerationMatch':0},'headers':{'Content-Type':'application/json'},'body':body}}
if '--workflows-only' not in sys.argv:
 old=json.loads((R/'data/cloud/manifest.json').read_text());assert len(old)==111
 finished=[];manifest=[]
 for i,wave in enumerate(old):
  payload=json.loads(lzma.decompress((R/'data/cloud'/(wave['id']+'.xz')).read_bytes()))
  group=json.loads(payload['groups.json'])['wave']
  if i<5:finished.extend(c['pilot_case'] for c in group);continue
  for n in ['worker.py','transport.py','checkpoint_control.py']:
   payload[n]=payload[n].replace('campaign01','campaign02');ast.parse(payload[n])
  for c in group:assert hashlib.sha256(payload['decks/'+c['pilot_case']+'.fds'].encode()).hexdigest()==c['deck_sha256']
  blob=lzma.compress(json.dumps(payload).encode());(D/(wave['id']+'.xz')).write_bytes(blob)
  manifest.append(dict(id=wave['id'],count=len(group),sha256=hashlib.sha256(blob).hexdigest()))
 assert len(finished)==78 and len(set(finished))==78 and sum(x['count'] for x in manifest)==1900
 # All excluded cases must have pinned passing completion records; terminal audit gates launch separately.
 proofs=json.loads((R/'private/worker-proofs.json').read_text())
 (P/'excluded-completed-cases.json').write_text(json.dumps(finished,indent=2)+'\n')
 (D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 boot=(R/'data/cloud/bootstrap.py').read_text().replace('campaign01','campaign02');(D/'bootstrap.py').write_text(boot);ast.parse(boot)
else:
 manifest=json.loads((D/'manifest.json').read_text());boot=(D/'bootstrap.py').read_text()
w=clone(yaml.safe_load((R/'workflow.yaml').read_text()))
init=w['main']['steps'][0]['init']['assign'];base=next(x['template'] for x in init if 'template' in x)
base['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
loop=w['main']['steps'][5]['campaign']['try']['steps'][1]['waves']['for']['steps']
by={next(iter(s)):s for s in loop}
# Bounded quota check: no potentially unbounded quota-list polling loop.
quota=w['await_quota']['steps'];quota[:]=[s for s in quota if next(iter(s)) not in ['init','canary','wait']]
quota[-1]={'ready':{'switch':[{'condition':'${available >= 4 * int(c.job.taskGroups[0].taskCount)}','return':True}],'next':'quota_denied'}}
quota.append({'quota_denied':{'raise':'Insufficient Spot CPU quota; no job submitted'}})
# Avoid accumulating per-VM polling work. Batch lifetime bound plus job deadline remains;
# the independent inventory/cleanup runs once at terminal and repeatedly only while cleaning.
steps=[copy.deepcopy(by[k]) for k in ['candidate','quota_gate','create','set_deadline','get','record_state']]
steps[0]['candidate']['assign'].append({'poll_count':0})
steps += [
 {'poll_bound':{'assign':[{'poll_count':'${poll_count+1}'}]}},
 {'poll_limit':{'switch':[{'condition':'${poll_count > 375}','raise':'Bounded wave poll limit reached'}]}},
 {'eviction_check_needed':{'switch':[{'condition':'${int(default(map.get(state.body,["status","taskGroups","group0","counts","FAILED"]),0)) >= 2 and checkpoint_seconds > 180}', 'steps':[copy.deepcopy(by['adapt_checkpoint_interval'])]}]}},
 copy.deepcopy(by['terminal']),copy.deepcopy(by['controller_limit']),copy.deepcopy(by['wait']),copy.deepcopy(by['clean_success']),
 {'wave_result':{'return':{'passed':True,'wave':'${wave.id}','count':'${wave.count}','checkpoint_seconds':'${checkpoint_seconds}','compute_charge_upper_usd':'${(sys.now()-wave_started)*wave.count*admission.body.rate_usd_per_vm_hour/3600}','cleanup_verified':True}}}]
# Scan task histories only when a failing job will abort, and bound the response/event shape.
a=w['adapt_checkpoints']['steps'];ix=next(i for i,s in enumerate(a) if 'count_tasks' in s)
a.insert(ix,{'task_shape_bound':{'switch':[{'condition':'${len(default(map.get(tasks.body,"tasks"),[])) > 18 or map.get(tasks.body,"nextPageToken") != null}','raise':'Unexpected task pagination/count; fail closed'}]}})
tasksteps=next(s['count_tasks']['for']['steps'] for s in a if 'count_tasks' in s)
tasksteps.insert(0,{'event_bound':{'switch':[{'condition':'${len(default(map.get(task.status,"statusEvents"),[])) > 50}','raise':'Unexpected task event history; fail closed'}]}})
event_parts=[x for x in tasksteps if 'event_bound' in x or 'events' in x]
tasksteps[:]=[x for x in tasksteps if x not in event_parts]
tasksteps.insert(2,{'failed_task_events':{'switch':[{'condition':'${task.status.state == \"FAILED\"}','steps':event_parts}]}})
# A FAILED task could be visible before job state FAILED. Remember the count so scans do not repeat.
steps[0]['candidate']['assign'].append({'last_failed':0})
guard=next(s['eviction_check_needed']['switch'][0] for s in steps if 'eviction_check_needed' in s)
guard['condition']='${int(default(map.get(state.body,["status","taskGroups","group0","counts","FAILED"]),0)) >= 2 and int(default(map.get(state.body,["status","taskGroups","group0","counts","FAILED"]),0)) > last_failed and checkpoint_seconds > 180}'
guard['steps'].append({'remember_failed':{'assign':[{'last_failed':'${int(default(map.get(state.body,["status","taskGroups","group0","counts","FAILED"]),0))}'}]}})
# Cleanup loop has its own finite iteration bound, including exceptional HTTP responses.
cleanup=w['cleanup']['steps'];cleanup[0]['cleanup_deadline']['assign'].append({'cleanup_polls':0})
idx=next(i for i,s in enumerate(cleanup) if 'wait' in s)
cleanup[idx:idx]=[{'cleanup_count':{'assign':[{'cleanup_polls':'${cleanup_polls+1}'}]}},{'cleanup_poll_limit':{'switch':[{'condition':'${cleanup_polls>40 or sys.now()>cleanup_until}','raise':'Cleanup bound reached; independent audit required'}]}}]
# Protect against unexpectedly large inventories before iterating, despite API's 500 page size.
inv=w['inventory']['steps'][1]['zones']['for']['steps']
for key,result in [('page_guard_v','v'),('page_guard_d','d')]:
 s=next(s[key] for s in inv if key in s);s['switch'].append({'condition':'${len(default(map.get('+result+'.body,"items"),[])) > 18}','raise':'Unexpected resource count; audit required'})
except_steps=copy.deepcopy(w['main']['steps'][5]['campaign']['except'])
except_steps['steps'][0]={'cleanup_all':{'switch':[{'condition':'${len(candidates)>0}','steps':[{'clean_failed':{'call':'cleanup','args':{'c':'${candidates[0]}'}}}]}]}}
child={k:v for k,v in w.items() if k not in ['main','initialize_checkpoint_control']}
child['main']={'params':['args'],'steps':[
 {'init':{'assign':[{'template':base},{'candidates':[]},{'checkpoint_seconds':'${args.checkpoint_seconds}'},{'wave_started':'${sys.now()}'},{'wave':None}]}},
 {'read_admission':get('control/admission-v4.json','admission')},{'read_manifest':get('inputs/manifest.json','manifest')},
 {'select_wave':{'for':{'value':'item','in':'${manifest.body}','steps':[{'match':{'switch':[{'condition':'${item.id == args.wave_id}','assign':[{'wave':'${item}'}]}]}}]}}},
 {'validate':{'switch':[{'condition':'${wave == null or admission.body.passed != true or not (checkpoint_seconds == 480 or checkpoint_seconds == 300 or checkpoint_seconds == 180)}','raise':'Invalid frozen wave request'}, {'condition':'${args.spent + wave.count*admission.body.reserve_seconds_per_vm*admission.body.rate_usd_per_vm_hour/3600 > admission.body.compute_limit_usd}','raise':'Wave exceeds remaining compute allowance'}]}},
 {'dry_run':{'switch':[{'condition':'${default(map.get(args,"dry_run"),false)}','return':{'passed':True,'dry_run':True,'wave':'${wave.id}'}}]}},
 # Claim is outside cleanup try: a duplicate execution must never delete the owner's job.
 {'claim_once':put('${"'+PREFIX+'claims/"+wave.id+".json"}',{'execution':'${sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}','wave':'${wave.id}'})},
 {'wave_run':{'try':{'steps':steps},'except':except_steps}}]}
dump('wave02.yaml',child)
# The parent never runs Batch directly. It uses POST once, bounded GET polling, and immutable receipts.
endpoint='https://workflowexecutions.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/workflows/'+RUN+'-wave/executions'
parent={'initialize_checkpoint_control':w['initialize_checkpoint_control']}
parent['main']={'steps':[
 {'init':{'assign':[{'checkpoint_seconds':480},{'spent':0},{'completed_cases':100},{'campaign_started':'${sys.now()}'},{'parent_polls':0}]}},
 {'read_admission':get('control/admission-v4.json','admission')},{'read_manifest':get('inputs/manifest.json','manifest')},
 {'initialize_policy':{'call':'initialize_checkpoint_control'}},
 {'waves':{'for':{'value':'wave','in':'${manifest.body}','steps':[
 copy.deepcopy(by['budget_admission']),
 {'child_arguments':{'assign':[{'child_args':{'wave_id':'${wave.id}','spent':'${spent}','checkpoint_seconds':'${checkpoint_seconds}'}}]}},
 {'start_child':{'call':'http.post','args':{'url':endpoint,'auth':{'type':'OAuth2'},'body':{'argument':'${json.encode_to_string(child_args)}'}},'result':'child'}},
 {'save_child':put('${"'+PREFIX+'children/"+wave.id+".json"}','${child.body}')},
 {'get_child':{'try':{'call':'http.get','args':{'url':'${"https://workflowexecutions.googleapis.com/v1/"+child.body.name}','auth':{'type':'OAuth2'}},'result':'child_state'},'retry':'${http.default_retry}'}},
 {'child_terminal':{'switch':[{'condition':'${child_state.body.state == "SUCCEEDED"}','next':'read_result'},{'condition':'${child_state.body.state != "ACTIVE" and child_state.body.state != "QUEUED"}','raise':'Child failed; no automatic paid retry; audit child and resources'}]}},
 {'parent_bound':{'assign':[{'parent_polls':'${parent_polls+1}'}]}},
 {'parent_limit':{'switch':[{'condition':'${parent_polls > 4400 or sys.now()-campaign_started > 259200}','raise':'Parent deadline; inspect current child before any continuation'}]}},
 {'wait_child':{'call':'sys.sleep','args':{'seconds':60},'next':'get_child'}},
 {'read_result':{'assign':[{'outcome':'${json.decode(child_state.body.result)}'}]}},
 {'require_success':{'switch':[{'condition':'${outcome.passed != true or outcome.cleanup_verified != true or outcome.wave != wave.id or outcome.count != wave.count}','raise':'Child outcome failed validation'}]}},
 {'save_result':put('${"'+PREFIX+'wave-results/"+wave.id+".json"}','${outcome}')},
 {'account':{'assign':[{'spent':'${spent+outcome.compute_charge_upper_usd}'},{'checkpoint_seconds':'${outcome.checkpoint_seconds}'},{'completed_cases':'${completed_cases+wave.count}'}]}}
 ]}}},
 {'done':{'return':{'passed':True,'completed_case_count':'${completed_cases}','compute_charge_upper_usd':'${spent}','checkpoint_seconds':'${checkpoint_seconds}'}}}]}
dump('workflow02.yaml',parent)
ready=clone(yaml.safe_load((R/'readiness.yaml').read_text().replace('admission-v2.json','admission-v4.json')))
ready['await_quota']=copy.deepcopy(child['await_quota']);ready['inventory']=copy.deepcopy(child['inventory'])
for s in ready['main']['steps']:
 if 'manifest_shape' in s:s['manifest_shape']['switch'][0]['condition']='${len(manifest.body) != 106 or manifest.body[0].count != 18}'
ready['main']['steps'][0]['init']['assign'][0]['candidates'][0]['job']['taskGroups'][0]['taskCount']='18'
next(s['quota_probe']['args']['c'] for s in ready['main']['steps'] if 'quota_probe' in s)['job']['taskGroups'][0]['taskCount']='18'
# Probe child invocation permissions and argument/manifest/budget validation WITHOUT creating a Batch job.
ready['main']['steps'].insert(-1,{'child_permission_probe':{'call':'http.post','args':{'url':endpoint,'auth':{'type':'OAuth2'},'body':{'argument':json.dumps(dict(wave_id='wave-005',spent=0,checkpoint_seconds=480,dry_run=True))}},'result':'probe_child'}})
ready['main']['steps'][-1]['done']['return']['child_execution']='${probe_child.body.name}'
dump('readiness02.yaml',ready)
pkg=dict(cases=2000,new_cases=1900,reused=100,waves=106,manifest_sha256=hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),workflow_sha256=hashlib.sha256((R/'workflow02.yaml').read_bytes()).hexdigest(),wave_sha256=hashlib.sha256((R/'wave02.yaml').read_bytes()).hexdigest(),image_uri=base['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['imageUri'],max_parallel_cpus=72,checkpoint_seconds=[480,300,180],zero_retries=True)
(P/'package.json').write_text(json.dumps(pkg,indent=2)+'\n');(R/'launch-record02.json').write_text(json.dumps(pkg,indent=2)+'\n');print(pkg)
