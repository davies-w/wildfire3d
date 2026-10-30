"""Prepare a second regional Spot queue; cloud arbitration permits one trainer only."""
from pathlib import Path
import json,hashlib,shutil,tarfile,base64,yaml
R=Path(__file__).resolve().parent;D=R/'data/training04';O=R/'results04';O.mkdir(exist_ok=True)
assert not (O/'submission-intent.json').exists()
D.mkdir(exist_ok=True)
old=json.loads((R/'results03/package.json').read_text())
for n,h in old['files'].items():
 src=R/'data/training03'/n;assert hashlib.sha256(src.read_bytes()).hexdigest()==h
 dst=D/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
p=D/'runtime.py';p.write_text(p.read_text().replace('history38/training03/','history38/training04/'))
files={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in old['files']}
assert all(files[n]==h for n,h in old['files'].items() if n!='runtime.py')
(D/'hashes.json').write_text(json.dumps(files,indent=2)+'\n')
with tarfile.open(D/'inputs.tar','w') as tar:
 for n in sorted([*files,'hashes.json']):tar.add(D/n,arcname=n)
digest=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()
boot=(R/'data/training03/bootstrap.py').read_text().replace('history38/training03/','history38/training04/').replace(old['input_sha256'],digest)
# Do not fit or even run startup optimizer probes before the controller grants ownership.
gate='''import time,urllib.error
for race_attempt in range(360):
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
 u='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/history38%2Ftraining04%2Frace-winner.json?alt=media'
 try:
  decision=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=30))
  assert decision['winner']=='history38-training04' and decision['oregon_cleanup_verified']
  break
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
 time.sleep(5)
else:raise RuntimeError('No cloud ownership grant within 30 minutes of worker startup; refusing duplicate training')
'''
boot=boot.replace("p=pathlib.Path('/tmp/study')",gate+"\np=pathlib.Path('/tmp/study')")
(D/'bootstrap.py').write_text(boot)
w=yaml.safe_load((R/'data/training03/workflow.yaml').read_text().replace('gpu38-history03','gpu38-history04').replace('history38/training03/','history38/training04/').replace('us-west1','us-central1').replace('fds-timing-west1','fds-trial'))
steps=w['main']['steps'];job=steps[0]['initialize']['assign'][0]['job']
job['allocationPolicy']['location']['allowedLocations']=['zones/us-central1-'+z for z in 'abcf']
job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
steps[0]['initialize']['assign'].append({'race_won':False})
# Expand existing two-zone inventory and cleanup to all four Iowa zones.
# Apply inventory extension separately to nested monitor and outer cleanup.
monitor=next(x['monitor']['try']['steps'] for x in steps if 'monitor'in x)
def add_zones(seq,stem,pool):
 template=next(x[stem+'_c'] for x in seq if stem+'_c'in x)
 append=next(x[stem+'_append_c'] for x in seq if stem+'_append_c'in x)
 i=next(i for i,x in enumerate(seq) if stem+'_c'in x)
 for suffix,zone in [('d','c'),('e','f')]:
  seq.insert(i+1,{stem+'_'+suffix:json.loads(json.dumps(template).replace('us-central1-b','us-central1-'+zone).replace(pool+'_c',pool+'_'+suffix))});i+=1
 i=next(i for i,x in enumerate(seq) if stem+'_append_c'in x)
 for suffix in ['d','e']:
  seq.insert(i+1,{stem+'_append_'+suffix:json.loads(json.dumps(append).replace(pool+'_c',pool+'_'+suffix).replace(stem+'_append_vm',stem+'_append_vm_'+suffix))});i+=1
add_zones(monitor,'get_vm','active_vms');add_zones(steps,'list_workers','workers');add_zones(steps,'verify','remaining')
PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial'
oldjob='https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-west1/jobs/fds-gpu38-history03'
oldexec=json.loads((R/'results03/execution.json').read_text())['name']
def http(method,url,result=None,**kw):
 v={'call':'http.'+method,'args':{'url':url,'auth':{'type':'OAuth2'},**kw}}
 if result:v['result']=result
 return v
def ignore404(spec,name):return {'try':spec,'except':{'as':name,'steps':[{'check_'+name:{'switch':[{'condition':'${map.get('+name+', "code") != 404}','raise':'${'+name+'}'}]}}]}}
# Arbitration occurs inside the cloud job supervisor, and also before creating Iowa.
w['arbitrate']={'params':['new_allocated'],'steps':[
 {'old_job':{'try':http('get',oldjob,'oj'),'except':{'as':'old_job_error','steps':[{'old_job_missing':{'switch':[{'condition':'${map.get(old_job_error, "code") == 404}','return':{'winner':'03','reason':'Original job is terminal or removed; do not train duplicate'}},{'condition':'${true}','raise':'${old_job_error}'}]}}]}}},
 {'old_workers':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-west1-a/instances','ov',query={'filter':'labels.trial_id = gpu38-history03'})},
 {'choose':{'switch':[
 {'condition':'${len(default(map.get(ov.body, "items"), [])) > 0 or oj.body.status.state == "RUNNING" or oj.body.status.state == "SUCCEEDED"}','return':{'winner':'03','reason':'Oregon allocated or already terminal'}},
 {'condition':'${not new_allocated}','return':{'winner':'waiting'}},
 ]}},
 {'save_original':http('post','https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',query={'uploadType':'media','name':'history38/training04/oregon-before-cancellation.json'},headers={'Content-Type':'application/json'},body='${oj.body}')},
 {'delete_original_queue':ignore404(http('delete',oldjob),'delete_old_error')},
 {'wait_original_cleanup':{'call':'sys.sleep','args':{'seconds':10}}},
 {'old_workers_after':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-west1-a/instances','ova',query={'filter':'labels.trial_id = gpu38-history03'})},
 {'old_disks_after':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-west1-a/disks','oda',query={'filter':'labels.trial_id = gpu38-history03'})},
 {'reset_old_removed':{'assign':[{'old_removed':False}]}},
 {'old_jobs_after':{'try':http('get',oldjob,'oja'),'except':{'as':'old_gone','steps':[{'check_old_gone':{'switch':[{'condition':'${map.get(old_gone, "code") == 404}','assign':[{'old_removed':True}]},{'condition':'${true}','raise':'${old_gone}'}]}}]}}},
 {'ensure_original_empty':{'switch':[{'condition':'${len(default(map.get(ova.body, "items"), [])) > 0 or len(default(map.get(oda.body, "items"), [])) > 0 or not old_removed}','next':'wait_original_cleanup'}]}},
 {'grant':http('post','https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',query={'uploadType':'media','name':'history38/training04/race-winner.json','ifGenerationMatch':0},headers={'Content-Type':'application/json'},body={'winner':'history38-training04','oregon_cleanup_verified':True,'original_status':'${oj.body.status}','selected_at':'${time.format(sys.now())}'})},
 {'won':{'return':{'winner':'04'}}}
]}
steps.insert(1,{'before_create':{'call':'arbitrate','args':{'new_allocated':False},'result':'choice'}})
steps.insert(2,{'original_already_won':{'switch':[{'condition':'${choice.winner == "03"}','return':'Oregon already allocated; Iowa not submitted'}]}})
i=next(i for i,x in enumerate(monitor) if 'reset_age'in x)
monitor[i:i]=[
 {'skip_arbitration':{'switch':[{'condition':'${race_won}','next':'reset_age'}]}},
 {'race_check':{'call':'arbitrate','args':{'new_allocated':'${len(default(map.get(active_vms.body, "items"), [])) > 0}'},'result':'choice'}},
 {'race_result':{'switch':[{'condition':'${choice.winner == "03"}','next':'record'},{'condition':'${choice.winner == "04"}','assign':[{'race_won':True}]}]}}
]
# Keep allocation race polling responsive; no allocation timeout.
next(x['wait']['args'] for x in monitor if 'wait'in x)['seconds']=30
(D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
proof={**old,'files':files,'input_sha256':digest,'input_bytes':(D/'inputs.tar').stat().st_size,'workflow_sha256':hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),'region':'us-central1','zones':job['allocationPolicy']['location']['allowedLocations'],'race_with':'history38-training03','worker_requires_ownership_grant':True,'model_recipe_byte_identical':True}
(O/'package.json').write_text(json.dumps(proof,indent=2)+'\n')
for name in ['monitor','audit_startup','collect','close']:
 s=(R/(name+'03.py')).read_text().replace('training03','training04').replace('results03','results04').replace('history03','history04').replace('audit03','audit04').replace('us-west1','us-central1')
 # Baseline reference remains the published rotation0 training03.
 s=s.replace("prior/'results04/package.json'","prior/'results03/package.json'")
 if name=='collect':
  s=s.replace("['results/package.json','results04/package.json','results04/package.json','results04/package.json'", "['results/package.json','results03/package.json','results03/package.json','results04/package.json'")
  s=s.replace("['training04','training04','training06']","['training03','training04','training06']")
  s=s.replace("  transfer=check_transfer_bound", "  extra_inputs+=json.loads((R/'results03/package.json').read_text())['input_bytes']\n  prior_output+=2*1024**3 # Bound any not-yet-collected Oregon competitor output.\n  transfer=check_transfer_bound")
 (R/(name+'04.py')).write_text(s)
print(json.dumps({k:v for k,v in proof.items() if k!='files'}))
