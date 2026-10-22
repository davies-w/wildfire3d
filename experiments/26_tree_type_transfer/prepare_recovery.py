"""Explicit bounded recovery approved by user's 'so go'; no automatic retry."""
import json,hashlib,shutil,base64,lzma,yaml,re
from pathlib import Path
from cloud import ROOT,read,save,verify
assert read('budget.json')['reserved_usd']==1.8
assert not (ROOT/'results/prediction-freeze.json').exists()
audit=ROOT/'results/original-inputs';audit.mkdir(exist_ok=False)
for name in ['build.py','cases.json','groups.json','results/input-freeze.json']:
 shutil.copy(ROOT/name,audit/Path(name).name)
# Fix only the six invalid inputs; completed and test deck bytes stay unchanged.
p=ROOT/'build.py';s=p.read_text();needle=" s=re.sub(r'&PART"
pos=s.index(needle)
s=s[:pos]+" if c['duration']==25:\n  s=re.sub(r\"&SURF ID='IGNITOR'.*?/\\n\",'',s,flags=re.S)\n  s=re.sub(r\"&RAMP ID='source'.*?/\\n\",'',s,flags=re.S)\n"+s[pos:];p.write_text(s)
import build
ts=read('data/tree-templates.json');cases=read('cases.json');freeze=read('results/input-freeze.json');changed=[]
for c in cases:
 text,_=build.deck(c,ts);h=hashlib.sha256(text.encode()).hexdigest()
 if h!=c['deck_sha256']:
  assert c['duration']==25 and c['family']=='single'
  assert text==(ROOT/'data/repair-preflight'/c['case']/'candidate.fds').read_text()
  shutil.copy(ROOT/'decks'/(c['case']+'.fds'),audit/(c['case']+'.fds'))
  (ROOT/'decks'/(c['case']+'.fds')).write_text(text);c['deck_sha256']=h;freeze['cases'][c['case']]=h;changed.append(c['case'])
assert len(changed)==6
save('cases.json',cases);save('results/input-freeze.json',freeze);verify()
missing=[c['case'] for c in cases if c['split'] in ['train','validation'] and not (ROOT/'data/cloud'/c['case']/'result.json').exists()]
assert len(missing)==9
new=[dict(id='t26-recovery-0',phase='development',cases=missing,duration_s=5400,allowance_usd=.2),dict(id='t26-test-combined',phase='test',cases=[c['case'] for c in cases if c['split'].endswith('test')],duration_s=5400,allowance_usd=.2)]
for g in new:
 name=g['id'];cs=[next(c for c in cases if c['case']==n) for n in g['cases']]
 runner=(ROOT/'runner-template.py').read_text().replace('overnight21/overnight21_stronger/',f'transfer26/{name}/').replace('400*1024**2','500*1024**2').replace('timeout=90','timeout=300')
 payload={'runner.py':runner,'worker.py':(ROOT/'worker.py').read_text(),'cases.json':json.dumps(cs),'group.json':json.dumps(g),'build.py':(ROOT/'build.py').read_text(),'base-input.fds':(ROOT/'base-input.fds').read_text(),'reference-particles.json':json.dumps({k:v[:400] for k,v in read('reference-particles.json').items()}),'input-freeze.json':json.dumps(freeze)}
 encoded=base64.b64encode(lzma.compress(json.dumps(payload).encode(),preset=9)).decode()
 bootstrap="import json,lzma,base64,pathlib,sys,runpy; root=pathlib.Path('/study'); payload=json.loads(lzma.decompress(base64.b64decode("+repr(encoded)+"))); [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_text(v) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
 w=read('workflow-template.json');ass=w['main']['steps'][0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + 5280}';job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']='5160s';task['runnables'][0]['container']['commands']=['-c',bootstrap];job['labels']['trial_id']=name;job['allocationPolicy']['labels']['trial_id']=name
 raw=json.dumps(w).replace('fds-controlled-trial','fds-'+name).replace('domain17/job-status.json',f'transfer26/{name}/job-status.json').replace('labels.trial_id = study17','labels.trial_id = '+name)
 folder=ROOT/'jobs'/name;folder.mkdir();(folder/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));save(f'jobs/{name}/group.json',g)
save('groups.json',read('groups.json')+new)
save('results/recovery-plan.json',dict(changed_inputs=changed,missing_cases=missing,new_groups=new,original_reserved_usd=1.8,additional_allowance_usd=.4,total_cap_usd=2.2,physics_change='None; removed unused invalid ramp/surface only',template_sha256=freeze['template_sha256'],cost_basis='Each 90min at .08USD/hour=.12 compute plus .08 ancillary/cleanup; no failed reservations recycled'))
print('Prepared recovery and combined tests; no submission yet')
