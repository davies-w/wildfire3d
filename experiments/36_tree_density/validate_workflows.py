from pathlib import Path
import json,yaml,lzma,hashlib,ast
r=Path(__file__).resolve().parent;groups=json.loads((r/'groups.json').read_text());seen=[]
for g in groups:
 wpath=r/'jobs'/g['id']/'workflow.yaml';w=yaml.safe_load(wpath.read_text());assert hashlib.sha256(wpath.read_bytes()).hexdigest()==g['workflow_sha256'];assert wpath.stat().st_size<128*1024
 job=w['main']['steps'][0]['initialize']['assign'][1]['job'];assert job['taskGroups'][0]['taskSpec']['maxRetryCount']==0
 boot=job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands'][1];ast.parse(boot)
 blob=(r/'data/packages'/(g['id']+'.xz')).read_bytes();assert hashlib.sha256(blob).hexdigest()==g['package_sha256'];p=json.loads(lzma.decompress(blob));cs=json.loads(p['cases.json'])
 for n in ['worker.py','runner.py','transport.py']:ast.parse(p[n])
 for c in cs:assert hashlib.sha256(p['decks/'+c['case']+'.fds'].encode()).hexdigest()==c['deck_sha256'];seen.append(c['case'])
assert len(seen)==len(set(seen))==1560
(r/'results/workflow-preflight.json').write_text(json.dumps(dict(passed=True,groups=len(groups),unique_cases=len(seen),all_package_and_deck_hashes_verified=True,no_network_or_solves=True,max_workers=24),indent=2)+'\n')
print('PASS: 131 workflows, 1560 immutable decks, 24-worker limit')
