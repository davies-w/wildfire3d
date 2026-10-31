"""Build a single cloud controller with three ownership-gated regional queues."""
from pathlib import Path
import copy, json, hashlib, tarfile, base64, yaml, ast
R=Path(__file__).resolve().parent; B=R.parent/'38_history8_shared64'; D=R/'data/training'; O=R/'results'; O.mkdir(exist_ok=True)
assert not (O/'submission-intent.json').exists()
PROJECT='tmrw-wildfire-20261015'; BUCKET=PROJECT+'-trial'; PREFIX='dropout40/pool01/'; WF='fds-gpu40-pool01'
s=(R.parent/'39_long_window_continuation/data/training02/cloud_check.py').read_text().replace("ck['epoch']==109","ck['epoch']==159").replace('source_epoch=109,next_epoch=110','source_epoch=159,next_epoch=160').replace('epoch110','epoch160').replace('for h in (64,90):','for h in (90,):').replace('[(64,20),(90,271)]','[(90,241)]')
(D/'cloud_check.py').write_text(s)
p=D/'runtime.py';p.write_text(p.read_text().replace("PREFIX='dropout40/training01/'", "import os\nPREFIX=os.environ['OUTPUT_PREFIX']"))
files={str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(D.rglob('*')) if f.is_file() and f.name not in ['hashes.json','inputs.tar','workflow.yaml','bootstrap.py']}
(D/'hashes.json').write_text(json.dumps(files,indent=2)+'\n')
with tarfile.open(D/'inputs.tar','w') as tar:
 for n in [*files,'hashes.json']:tar.add(D/n,arcname=n)
digest=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()
boot=(B/'data/training08/bootstrap.py').read_text().replace('history38/training08/inputs.tar',PREFIX+'inputs.tar').replace('1a0db7e18981f80b9783ca305d35fde2422188cdf85709668d0d51f9bd6e2c2b',digest)
gate='''import os,time,urllib.error
for attempt in range(360):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 tok=json.load(urllib.request.urlopen(req,timeout=20))['access_token']
 url='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/dropout40%2Fpool01%2Frace-winner.json?alt=media'
 try:
  decision=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+tok}),timeout=30))
  assert decision['winner']==os.environ['CANDIDATE_ID'] and decision['losers_cleanup_verified']
  break
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
 time.sleep(5)
else:raise RuntimeError('No ownership grant within 30 minutes; no optimizer work permitted')
'''
boot=boot.replace("p=pathlib.Path('/tmp/study')",gate+"\np=pathlib.Path('/tmp/study')")
(D/'bootstrap.py').write_text(boot)
base=yaml.safe_load((B/'data/training08/workflow.yaml').read_text())['main']['steps'][0]['initialize']['assign'][0]['job']
candidates=[]
for suffix,region,zones,network,subnet in [('or','us-west1','ab','fds-trial','fds-timing-west1'),('ia','us-central1','abcf','fds-trial','fds-trial'),('sc','us-east1','bcd','default','default')]:
 label='gpu40-pool01-'+suffix;job=copy.deepcopy(base);task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']='49500s';task['environment']={'variables':{'TRAINING_SOFT_SECONDS':'48600','OUTPUT_PREFIX':PREFIX+suffix+'/','CANDIDATE_ID':suffix}}
 task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
 policy=job['allocationPolicy'];policy['location']['allowedLocations']=['zones/'+region+'-'+z for z in zones];policy['labels']['trial_id']=label;job['labels']['trial_id']=label
 policy['network']['networkInterfaces']=[{'network':f'projects/{PROJECT}/global/networks/{network}','subnetwork':f'projects/{PROJECT}/regions/{region}/subnetworks/{subnet}'}]
 candidates.append(dict(id=suffix,region=region,zones=[region+'-'+z for z in zones],label=label,job_id='fds-'+label,job=job))

def http(method,url,result=None,**kw):
 d={'call':'http.'+method,'args':{'url':url,'auth':{'type':'OAuth2'},**kw}}
 if result:d['result']=result
 return d
JOB='${"https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/" + c.region + "/jobs/" + c.job_id}'
COMPUTE='https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/'
ignore_count=0
def ignore404(call):
 global ignore_count
 ignore_count+=1
 return {'try':call,'except':{'as':'err','steps':[{'unexpected_'+str(ignore_count):{'switch':[{'condition':'${map.get(err,"code") != 404}','raise':'${err}'}]}}]}}
def record(name,body):
 if name.startswith('${'):
  name=name[:-1]+' + "." + string(sys.now())}'
 return http('post','https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',query={'uploadType':'media','name':name},headers={'Content-Type':'application/json'},body=body)
# Inventory deliberately reads every allowed zone, including disks, not only Batch state.
inventory={'params':['c'],'steps':[
 {'init':{'assign':[{'vms':[]},{'disks':[]}]}},
 {'zones':{'for':{'value':'z','in':'${c.zones}','steps':[
  {'get_vms':http('get','${"'+COMPUTE+'" + z + "/instances"}','v',query={'filter':'${"labels.trial_id = " + c.label}'})},
  {'append_vms':{'for':{'value':'vm','in':'${default(map.get(v.body,"items"),[])}','steps':[{'add_vm':{'assign':[{'vms':'${list.concat(vms,vm)}'}]}}]}}},
  {'get_disks':http('get','${"'+COMPUTE+'" + z + "/disks"}','d',query={'filter':'${"labels.trial_id = " + c.label}'})},
  {'append_disks':{'for':{'value':'disk','in':'${default(map.get(d.body,"items"),[])}','steps':[{'add_disk':{'assign':[{'disks':'${list.concat(disks,disk)}'}]}}]}}}
 ]}}}, {'done':{'return':{'vms':'${vms}','disks':'${disks}'}}}]}
cleanup={'params':['c'],'steps':[
 {'delete_job':ignore404(http('delete',JOB))},
 {'inventory':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}},
 {'delete_vms':{'for':{'value':'vm','in':'${inv.vms}','steps':[{'delete_vm':ignore404(http('delete','${vm.selfLink}'))}]}}},
 {'wait':{'call':'sys.sleep','args':{'seconds':15}}},
 {'verify':{'call':'inventory','args':{'c':'${c}'},'result':'left'}},
 {'empty':{'switch':[{'condition':'${len(left.vms) > 0 or len(left.disks) > 0}','next':'wait'}]}},
 {'job_present':{'assign':[{'present':True}]}},
 {'verify_job':{'try':http('get',JOB,'remaining'),'except':{'as':'e','steps':[{'gone':{'switch':[{'condition':'${map.get(e,"code") == 404}','assign':[{'present':False}]},{'condition':'${true}','raise':'${e}'}]}}]}}},
 {'job_wait':{'switch':[{'condition':'${present}','next':'wait'}]}},
 {'done':{'return':{'empty':True}}}]}
inner=[
 {'create_jobs':{'for':{'value':'c','in':'${candidates}','steps':[{'create':http('post','${"https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/" + c.region + "/jobs"}','created',query={'jobId':'${c.job_id}'},body='${c.job}')}]}}},
 {'reset':{'assign':[{'viable':0}]}},
 {'scan':{'for':{'value':'c','in':'${candidates}','steps':[
  {'get':http('get',JOB,'state')},
  {'save_status':record('${"'+PREFIX+'" + c.id + "/job-status.json"}','${state.body}')},
  {'inv':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}},
  {'eligible':{'switch':[{'condition':'${state.body.status.state != "FAILED" and state.body.status.state != "SUCCEEDED"}','steps':[
   {'increment':{'assign':[{'viable':'${viable+1}'}]}},
   {'choose':{'switch':[{'condition':'${winner == null and len(inv.vms) > 0 and inv.vms[0].status == "RUNNING"}','assign':[{'winner':'${c}'}]}]}}
  ]}]}}
 ]}}},
 {'selected':{'switch':[{'condition':'${winner != null}','next':'remove_losers'},{'condition':'${viable == 0}','raise':'All regional jobs failed before ownership grant'}]}},
 {'queue_wait':{'call':'sys.sleep','args':{'seconds':30},'next':'reset'}},
 {'remove_losers':{'for':{'value':'c','in':'${candidates}','steps':[{'loser':{'switch':[{'condition':'${c.id != winner.id}','steps':[{'clean':{'call':'cleanup','args':{'c':'${c}'}}}]}]}}]}}},
 {'grant':http('post','https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',query={'uploadType':'media','name':PREFIX+'race-winner.json','ifGenerationMatch':0},headers={'Content-Type':'application/json'},body={'winner':'${winner.id}','losers_cleanup_verified':True,'selected_at':'${time.format(sys.now())}'})},
 {'set_current':{'assign':[{'current':'${winner}'}]}},
 {'running':http('get',JOB.replace('c.region','current.region').replace('c.job_id','current.job_id'),'state')},
 {'save_winner_status':record('${"'+PREFIX+'" + current.id + "/job-status.json"}','${state.body}')},
 {'terminal':{'switch':[{'condition':'${state.body.status.state == "SUCCEEDED" or state.body.status.state == "FAILED"}','next':'finished'}]}},
 {'allocated':{'call':'inventory','args':{'c':'${current}'},'result':'inv'}},
 {'age_check':{'for':{'value':'vm','in':'${inv.vms}','steps':[{'overdue':{'switch':[{'condition':'${sys.now() >= time.parse(vm.creationTimestamp) + 50400}','raise':'VM lifetime limit reached; preserve completed checkpoints'}]}}]}}},
 {'training_wait':{'call':'sys.sleep','args':{'seconds':30},'next':'running'}},
 {'finished':{'assign':[{'final_state':'${state.body.status.state}'}]}}
]
w={'main':{'steps':[
 {'initialize':{'assign':[{'candidates':candidates},{'winner':None},{'final_state':'UNKNOWN'}]}},
 {'race':{'try':{'steps':inner},'except':{'as':'failure','steps':[
  {'save_failure':record(PREFIX+'controller-error.json','${failure}')},
  {'cleanup_failed':{'for':{'value':'c','in':'${candidates}','steps':[{'clean_failed':{'call':'cleanup','args':{'c':'${c}'}}}]}}},
  {'rethrow':{'raise':'${failure}'}}
 ]}}},
 {'cleanup_terminal':{'for':{'value':'c','in':'${candidates}','steps':[{'clean_terminal':{'call':'cleanup','args':{'c':'${c}'}}}]}}},
 {'done':{'return':{'winner':'${winner.id}','batch_state':'${final_state}','cleanup_verified':True}}}
]},'inventory':inventory,'cleanup':cleanup}
(R/'pool01.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
# Read-only cloud preflight exercises the identical inventory subworkflow in every zone.
ready={'main':{'steps':[{'init':{'assign':[{'candidates':candidates}]}},{'all':{'for':{'value':'c','in':'${candidates}','steps':[{'inspect':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}},{'empty':{'switch':[{'condition':'${len(inv.vms)>0 or len(inv.disks)>0}','raise':'Existing pool resources; reconcile before submission'}]}}]}}},{'done':{'return':{'passed':True}}}]},'inventory':inventory}
ready['main']['steps'].insert(1, {'write_probe1': record('${"'+PREFIX+'preflight-status"}', {'passed':True})})
ready['main']['steps'].insert(2, {'write_probe2': record('${"'+PREFIX+'preflight-status"}', {'passed':True})})
(R/'readiness01.yaml').write_text(yaml.safe_dump(ready,sort_keys=False))
for f in D.glob('*.py'):ast.parse(f.read_text())
proof=dict(input_sha256=digest,input_bytes=(D/'inputs.tar').stat().st_size,files=files,workflow_sha256=hashlib.sha256((R/'pool01.yaml').read_bytes()).hexdigest(),workflow=WF,prefix=PREFIX,candidates=[{k:v for k,v in c.items() if k!='job'} for c in candidates],resume_epoch=159,resume_sha256=hashlib.sha256((D/'data/resume/fold00.pt').read_bytes()).hexdigest(),soft_seconds=48600,task_seconds=49500,vm_seconds=50400,allowance_per_candidate_usd=11.2)
(O/'package.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Built three-region pool; every bootstrap requires the single ownership grant')
