"""Package unique one-case recovery; no cloud mutation or solver execution."""
from cloud48_05 import *
import yaml,lzma,copy,base64,ast
Q=R/'private07';assert not (Q/'submission-intent.json').exists()
plan=json.loads((Q/'recovery-plan.json').read_text())['cases'];assert len(plan)==1 and all('_fine' not in x['case']['pilot_case'] for x in plan)
old=json.loads(lzma.decompress((R/'data/cloud05/input.xz').read_bytes()));D=R/'data/cloud07';D.mkdir(exist_ok=True)
recovery={x['case']['pilot_case']:{k:x[k] for k in ['saved_step','saved_time_s','checkpoint_files','archive_parts']} for x in plan}
for x in recovery.values():
 x['archive_parts']=[{k:v[k] for k in ['name','generation','bytes','sha256']} for v in x['archive_parts']]
payload={'worker.py':(R/'recovery_worker06.py').read_text(),'pilot_worker06.py':(R/'pilot_worker06.py').read_text(),'transport.py':(R/'transport.py').read_text().replace('tree48/pilot01/','tree48/pilot07/'),'groups.json':json.dumps({'bulk':[x['case'] for x in plan]}),'recovery.json':json.dumps(recovery)}
for x in plan:
 n='decks/'+x['case']['pilot_case']+'.fds';payload[n]=old[n];assert hashlib.sha256(payload[n].encode()).hexdigest()==x['case']['deck_sha256']
for n,s in payload.items():
 if n.endswith('.py'):ast.parse(s)
(D/'input.xz').write_bytes(lzma.compress(json.dumps(payload).encode()));digest=sha(D/'input.xz')
boot=(R/'data/cloud05/bootstrap.py').read_text().replace('tree48/pilot05/','tree48/pilot07/').replace(json.loads((P/'package.json').read_text())['input_sha256'],digest);ast.parse(boot);(D/'bootstrap.py').write_text(boot)
original=yaml.safe_load((R/'pilot05.yaml').read_text());w=yaml.safe_load((R/'supervisor05.yaml').read_text());c=copy.deepcopy(original['main']['steps'][0]['init']['assign'][0]['candidates'][0]);t=c['job']['taskGroups'][0];t['taskCount']='1';t['parallelism']='1';t['taskSpec']['maxRunDuration']='18000s';t['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
w['main']['steps'][0]['init']['assign'][0]['candidates']=[c]
steps=w['main']['steps'][1]['campaign']['try']['steps'][0]['waves']['for']['steps'];orig=original['main']['steps'][1]['campaign']['try']['steps'][0]['waves']['for']['steps']
steps[:0]=[copy.deepcopy(x) for x in orig if 'quota_gate' in x or 'create' in x]
for x in steps:
 if 'set_deadline' in x:x['set_deadline']['assign']=[{'deadline':'${sys.now()+21600}'}]
 if 'check_age' in x:x['check_age']=json.loads(json.dumps(x['check_age']).replace('+11100','+18300'))
w['await_quota']=copy.deepcopy(original['await_quota']);w['main']['steps'][-1]['done']['return']['cases']=1
w=json.loads(json.dumps(w).replace('tree48/pilot05/','tree48/pilot07/').replace('tree48-pilot05','tree48-pilot07').replace('available >= 80','available >= 4'))
(R/'pilot07.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
r=yaml.safe_load((R/'readiness05.yaml').read_text());r=json.loads(json.dumps(r).replace('tree48/pilot05/','tree48/pilot07/').replace('tree48-pilot05','tree48-pilot07').replace('available >= 80','available >= 4'))
cs=w['main']['steps'][0]['init']['assign'][0]['candidates'];r['main']['steps'][0]['init']['assign'][0]['candidates']=copy.deepcopy(cs);r['inventory']=copy.deepcopy(w['inventory']);r['await_quota']=copy.deepcopy(w['await_quota'])
for x in r['main']['steps']:
 if 'quota_probe' in x:x['quota_probe']['args']['c']=copy.deepcopy(cs[0])
(R/'readiness07.yaml').write_text(yaml.safe_dump(r,sort_keys=False))
pkg=dict(input_sha256=digest,workflow_sha256=sha(R/'pilot07.yaml'),image_uri=json.loads((P/'package.json').read_text())['image_uri'],cases=1,case_ids=[x['case']['pilot_case'] for x in plan],max_solve_seconds=14400,max_task_seconds=18000,zero_retries=True,continuation_only=True)
(Q/'package.json').write_text(json.dumps(pkg,indent=2));(R/'launch-record07.json').write_text(json.dumps(pkg,indent=2));print(pkg)
