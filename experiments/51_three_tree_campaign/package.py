"""Freeze per-wave inputs and a remote budget-limited controller; no cloud submission."""
from pathlib import Path
import ast,base64,copy,hashlib,json,lzma,yaml
from build_controller import build,R,RUN,PREFIX,BUCKET
class NoAlias(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
P=R/'private';D=R/'data/cloud';D.mkdir(exist_ok=True)
assert not (P/'submission-intent.json').exists(),'Never repackage a submitted execution'
cases=json.loads((R/'data/decks/cases.json').read_text());assert len(cases)==1978
# One new case per oak size and one each for pine/eucalyptus precede bulk waves.
canaries=[]
for typ,gid in [(1,None),(3,None)]+[(2,f't2_r{r}_h{h}') for r in [6,7] for h in [10,11]]:
 canaries.append(next(c for c in cases if c['type_id']==typ and (gid is None or c['geometry_id']==gid)))
ids={c['case'] for c in canaries};left=[c for c in cases if c['case'] not in ids]
groups=[canaries]+[left[i:i+18] for i in range(0,len(left),18)]
worker={n:(R/n).read_text() for n in ['worker.py','transport.py','checkpoint_control.py']}
for s in worker.values():ast.parse(s)
manifest=[]
for i,group in enumerate(groups):
 name=f'wave-{i:03d}';payload=dict(worker);payload['groups.json']=json.dumps({'wave':group})
 for c in group:
  deck=(R/'data/decks/decks'/(c['pilot_case']+'.fds')).read_text();assert hashlib.sha256(deck.encode()).hexdigest()==c['deck_sha256'];payload['decks/'+c['pilot_case']+'.fds']=deck
 blob=lzma.compress(json.dumps(payload).encode());(D/(name+'.xz')).write_bytes(blob)
 manifest.append(dict(id=name,count=len(group),sha256=hashlib.sha256(blob).hexdigest()))
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
boot='''import os,json,lzma,pathlib,urllib.request,hashlib,sys,runpy
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
tok=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
wave=os.environ['WAVE_ID'];assert wave.startswith('wave-') and wave[5:].isdigit()
r=urllib.request.Request('https://storage.googleapis.com/BUCKET/PREFIXinputs/'+wave+'.xz',headers={'Authorization':'Bearer '+tok})
blob=urllib.request.urlopen(r,timeout=120).read();assert hashlib.sha256(blob).hexdigest()==os.environ['WAVE_SHA']
payload=json.loads(lzma.decompress(blob));root=pathlib.Path('/study');root.mkdir(exist_ok=True)
for n,v in payload.items():
 p=root/n;assert p.is_relative_to(root) and '..' not in pathlib.Path(n).parts;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
case=json.loads(payload['groups.json'])['wave'][int(os.environ['BATCH_TASK_INDEX'])]
(root/'task.json').write_text(json.dumps({'case':case,'output_prefix':'PREFIX'+wave+'/'+case['pilot_case']+'/'}))
sys.path.insert(0,str(root));runpy.run_path(str(root/'worker.py'),run_name='__main__')
'''.replace('BUCKET',BUCKET).replace('PREFIX',PREFIX)
ast.parse(boot);(D/'bootstrap.py').write_text(boot)
base=yaml.safe_load((R.parent/'50_live_oak/workflow.yaml').read_text())['main']['steps'][0]['init']['assign'][0]['candidates'][0]
base=json.loads(json.dumps(base).replace('tree50-oak01','tree51-campaign01'))
base['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
base['job']['taskGroups'][0]['taskSpec']['environment']['variables']={}
w=build();w['main']['steps']=[{'init':{'assign':[{'checkpoint_seconds':480},{'spent':0},{'candidates':[]},{'template':base},{'campaign_started':'${sys.now()}'}]}},
 {'read_admission':{'call':'http.get','args':{'url':f'https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/tree51%2Fcampaign01%2Fcontrol%2Fadmission-v2.json','query':{'alt':'media'},'auth':{'type':'OAuth2'}},'result':'admission'}},
 {'admission_guard':{'switch':[{'condition':'${admission.body.passed != true}','raise':'Budget admission missing'}]}},
 {'read_manifest':{'call':'http.get','args':{'url':f'https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/tree51%2Fcampaign01%2Finputs%2Fmanifest.json','query':{'alt':'media'},'auth':{'type':'OAuth2'}},'result':'manifest'}},
 {'load_manifest':{'assign':[{'waves':'${manifest.body}'}]}},
 copy.deepcopy(w['main']['steps'][2]),
 {'done':{'return':{'passed':True,'new_cases':1978,'reused_cases':22,'compute_charge_upper_usd':'${spent}','cleanup_verified':True}}}]
loop=w['main']['steps'][5]['campaign']['try']['steps'][1]['waves']['for'];loop['value']='wave';loop['in']='${waves}'
steps=loop['steps'];steps[:0]=[
 {'budget_admission':{'switch':[{'condition':'${spent + wave.count * admission.body.reserve_seconds_per_vm * admission.body.rate_usd_per_vm_hour / 3600 > admission.body.compute_limit_usd}', 'return':{'passed':False,'reason':'BUDGET_STOP','compute_charge_upper_usd':'${spent}','next_wave':'${wave.id}','completed_case_count':'${completed_cases}'}},{'condition':'${sys.now()-campaign_started > 259200}','raise':'Campaign deadline reached'}]}},
 {'candidate':{'assign':[{'c':'${template}'},{'c.id':'${wave.id}'},{'c.job_id':'${"'+RUN+'-"+wave.id}'},{'c.label':'${"tree51-campaign01-"+wave.id}'},{'c.job.taskGroups[0].taskCount':'${string(wave.count)}'},{'c.job.taskGroups[0].parallelism':'${string(wave.count)}'},{'c.job.taskGroups[0].taskSpec.environment.variables':{'WAVE_ID':'${wave.id}','WAVE_SHA':'${wave.sha256}'}},{'c.job.labels.trial_id':'${c.label}'},{'c.job.allocationPolicy.labels.trial_id':'${c.label}'},{'candidates':'${[c]}'},{'wave_started':'${sys.now()}'}]}}]
w['main']['steps'][0]['init']['assign'].append({'completed_cases':22})
steps.append({'account_wave':{'assign':[{'spent':'${spent + (sys.now()-wave_started) * wave.count * admission.body.rate_usd_per_vm_hour / 3600}'},{'completed_cases':'${completed_cases+wave.count}'}]}})
# Conservative wave-wall accounting includes idle/cleanup time for every possible VM.
# A within-wave deadline reserves cleanup time; no wave may borrow training funds.
for step in steps:
 if 'set_deadline' in step:step['set_deadline']['assign']=[{'deadline':'${wave_started+11100}'}]
# A global wall deadline protects the worst-case per-wave compute reservation.
for sub in ['cleanup']:
 w[sub]['steps'].insert(0,{'cleanup_deadline':{'assign':[{'cleanup_until':'${sys.now()+600}'}]}})
 ix=next(i for i,x in enumerate(w['cleanup']['steps']) if 'wait' in x)
w['cleanup']['steps'].insert(ix,{'cleanup_bound':{'switch':[{'condition':'${sys.now()>cleanup_until}','raise':'Cleanup requires audit; no next wave admitted'}]}})
w=json.loads(json.dumps(w).replace('available >= 32','available >= 72'))
(R/'workflow.yaml').write_text(yaml.dump(w,Dumper=NoAlias,sort_keys=False))
ready=yaml.safe_load((R.parent/'50_live_oak/readiness.yaml').read_text());ready=json.loads(json.dumps(ready).replace('tree50/oak01/',PREFIX).replace('tree50-oak01','tree51-campaign01').replace('available >= 32','available >= 72'))
probe=copy.deepcopy(base);probe['job_id']=RUN+'-wave-000';probe['label']='tree51-campaign01-wave-000';probe['id']='wave-000'
ready['main']['steps'][0]['init']['assign'][0]['candidates']=[probe]
ready['inventory']=copy.deepcopy(w['inventory']);ready['await_quota']=copy.deepcopy(w['await_quota'])
for step in ready['main']['steps']:
 if 'quota_probe' in step:step['quota_probe']['args']['c']=probe
(R/'readiness.yaml').write_text(yaml.dump(ready,Dumper=NoAlias,sort_keys=False))
pkg=dict(cases=2000,new_cases=1978,reused=22,waves=len(groups),manifest_sha256=hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),workflow_sha256=hashlib.sha256((R/'workflow.yaml').read_bytes()).hexdigest(),image_uri=base['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['imageUri'],max_parallel_cpus=72,checkpoint_seconds=[480,300,180],zero_retries=True)
(P/'package.json').write_text(json.dumps(pkg,indent=2)+'\n');(R/'launch-record.json').write_text(json.dumps(pkg,indent=2)+'\n');print(pkg)
