"""Prepare one bounded cloud test of the actual fine-grid checkpoint path."""
from cloud48_05 import *
import yaml,lzma,base64,copy,ast
Q=R/'private-stopcheck01';Q.mkdir(exist_ok=True);assert not (Q/'submission-intent.json').exists()
D=R/'data/stopcheck01';D.mkdir(exist_ok=True)
old=json.loads(lzma.decompress((R/'data/cloud05/input.xz').read_bytes()));case=next(c for c in json.loads(old['groups.json'])['bulk'] if c['pilot_case']=='tree48_000830_fine')
payload={'worker.py':(R/'checkpoint_probe01.py').read_text(),'pilot_worker06.py':(R/'pilot_worker06.py').read_text(),'transport.py':(R/'transport.py').read_text().replace('tree48/pilot01/','tree48/stopcheck01/'),'groups.json':json.dumps({'probe':[case]}),'decks/'+case['pilot_case']+'.fds':old['decks/'+case['pilot_case']+'.fds']}
(D/'input.xz').write_bytes(lzma.compress(json.dumps(payload).encode()));digest=sha(D/'input.xz')
boot=(R/'data/cloud05/bootstrap.py').read_text().replace('tree48/pilot05/','tree48/stopcheck01/').replace(json.loads((P/'package.json').read_text())['input_sha256'],digest);ast.parse(boot);(D/'bootstrap.py').write_text(boot)
original=yaml.safe_load((R/'pilot05.yaml').read_text());c=copy.deepcopy(original['main']['steps'][0]['init']['assign'][0]['candidates'][0]);c.update(id='probe',job_id='fds-tree48-stopcheck01-probe',label='tree48-stopcheck01-probe')
c['job']['labels']['trial_id']=c['label'];a=c['job']['allocationPolicy'];a['labels']['trial_id']=c['label']
t=c['job']['taskGroups'][0];t['taskCount']='1';t['parallelism']='1';ts=t['taskSpec'];ts['maxRunDuration']='3000s';ts['environment']['variables']['PILOT_GROUP']='probe';ts['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
w=yaml.safe_load((R/'supervisor05.yaml').read_text())
w=json.loads(json.dumps(w).replace('tree48/pilot05/','tree48/stopcheck01/').replace('fds-tree48-pilot05','fds-tree48-stopcheck01'))
w['main']['steps'][0]['init']['assign'][0]['candidates']=[c]
steps=w['main']['steps'][1]['campaign']['try']['steps'][0]['waves']['for']['steps']
create=copy.deepcopy(next(x for x in original['main']['steps'][1]['campaign']['try']['steps'][0]['waves']['for']['steps'] if 'create' in x));steps.insert(0,create)
for x in steps:
 if 'set_deadline' in x:x['set_deadline']['assign']=[{'deadline':'${sys.now()+3600}'}]
 if 'check_age' in x:x['check_age']=json.loads(json.dumps(x['check_age']).replace('+11100','+3300'))
w['main']['steps'][-1]['done']['return']['cases']=1
(R/'stopcheck01.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
pkg=dict(input_sha256=digest,workflow_sha256=sha(R/'stopcheck01.yaml'),case=case['pilot_case'],scope='One diagnostic fine-grid stop/upload/readback/resume; no full-case repeat',max_task_seconds=3000)
(Q/'package.json').write_text(json.dumps(pkg,indent=2)+'\n');(D/'validation.json').write_text(json.dumps(pkg,indent=2)+'\n');print(pkg)
