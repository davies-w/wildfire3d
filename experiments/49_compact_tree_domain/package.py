"""Freeze compact-domain inputs and a canary-gated controller; no cloud mutation."""
from cloud import *
import yaml,lzma,base64,copy,ast
assert not (P/'submission-intent.json').exists()
OLD=R.parent/'48_two_tree_design';D=R/'data/cloud';D.mkdir(exist_ok=True)
cases=json.loads((R/'data/cases.json').read_text());assert len(cases)==22
canary_ids={'tree49_000481_baseline','tree49_000500_baseline','tree49_001487_baseline','tree49_001500_baseline'}
groups={'canary':[x for x in cases if x['pilot_case'] in canary_ids],'bulk':[x for x in cases if x['pilot_case'] not in canary_ids]};assert [len(x) for x in groups.values()]==[4,18]
payload={'worker.py':(R/'worker.py').read_text(),'transport.py':(R/'transport.py').read_text(),'groups.json':json.dumps(groups)}
for c in cases:
 n='decks/'+c['pilot_case']+'.fds';payload[n]=(R/'data'/n).read_text();assert hashlib.sha256(payload[n].encode()).hexdigest()==c['deck_sha256']
for n,s in payload.items():
 if n.endswith('.py'):ast.parse(s)
(D/'input.xz').write_bytes(lzma.compress(json.dumps(payload).encode()));digest=sha(D/'input.xz')
boot=(OLD/'data/cloud07/bootstrap.py').read_text().replace('tree48/pilot07/','tree49/compact01/').replace(json.loads((OLD/'private07/package.json').read_text())['input_sha256'],digest);ast.parse(boot);(D/'bootstrap.py').write_text(boot)
w=yaml.safe_load((OLD/'pilot07.yaml').read_text());base=w['main']['steps'][0]['init']['assign'][0]['candidates'][0];candidates=[]
for group,cs in groups.items():
 c=copy.deepcopy(base);c['id']=group;c['job_id']=WF+'-'+group;c['label']='tree49-compact01-'+group;t=c['job']['taskGroups'][0];t['taskCount']=str(len(cs));t['parallelism']=str(len(cs));t['taskSpec']['maxRunDuration']='10800s';t['taskSpec']['environment']['variables']['PILOT_GROUP']=group;t['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
 c['job']['labels']['trial_id']=c['label'];c['job']['allocationPolicy']['labels']['trial_id']=c['label'];candidates.append(c)
w['main']['steps'][0]['init']['assign'][0]['candidates']=candidates;w['main']['steps'][-1]['done']['return']['cases']=22
w=json.loads(json.dumps(w).replace('tree48/pilot07/','tree49/compact01/').replace('tree48-pilot07','tree49-compact01').replace('available >= 4','available >= 72').replace('+18300','+11100').replace('+21600','+14400'))
(R/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
r=yaml.safe_load((OLD/'readiness07.yaml').read_text());r=json.loads(json.dumps(r).replace('tree48/pilot07/','tree49/compact01/').replace('tree48-pilot07','tree49-compact01').replace('available >= 4','available >= 72'));r['main']['steps'][0]['init']['assign'][0]['candidates']=copy.deepcopy(candidates);r['inventory']=copy.deepcopy(w['inventory']);r['await_quota']=copy.deepcopy(w['await_quota'])
for x in r['main']['steps']:
 if 'quota_probe' in x:x['quota_probe']['args']['c']=copy.deepcopy(candidates[-1])
(R/'readiness.yaml').write_text(yaml.safe_dump(r,sort_keys=False))
pkg=dict(input_sha256=digest,workflow_sha256=sha(R/'workflow.yaml'),image_uri=json.loads((OLD/'private07/package.json').read_text())['image_uri'],cases=22,groups={k:[c['pilot_case'] for c in v] for k,v in groups.items()},max_solve_seconds=7200,max_task_seconds=10800,zero_retries=True,matched_rerun=True)
save('package.json',pkg);(R/'launch-record.json').write_text(json.dumps(pkg,indent=2)+'\n');print('Packaged22 cases;4canary gate then18bulk')
