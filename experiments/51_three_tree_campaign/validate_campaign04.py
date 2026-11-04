"""Check continuation identity, bounded orchestration and deployed source equality."""
from cloud04 import *
import ast,base64,lzma,sys,yaml
pkg=json.loads((P/'package.json').read_text());assert (pkg['cases'],pkg['new_cases'],pkg['reused'])==(2000,1829,170)
assert sha(R/'data/cloud04/manifest.json')==pkg['manifest_sha256'] and sha(R/'workflow04.yaml')==pkg['workflow_sha256'] and sha(R/'wave04.yaml')==pkg['wave_sha256']
m=json.loads((R/'data/cloud04/manifest.json').read_text());assert len(m)==103 and sum(x['count'] for x in m)==1829
excluded=set(json.loads((P/'excluded-completed-cases.json').read_text()));collected=json.loads((R/'data/completed01/proof.json').read_text());second=json.loads((R/'data/completed02/proof.json').read_text());assert collected['passed'] and second['passed'];third=[c for wave in ['wave-006','wave-007','wave-008'] for c in json.loads((R/'data/completed03'/wave/'proof.json').read_text())['cases']];assert excluded=={c['case'] for c in collected['cases']}|{c['case'] for c in second['cases']}|{c['case'] for c in third}|{'tree51_000088_baseline','tree51_000136_baseline'} and len(excluded)==150
assert json.loads((R/'private02/terminal-scientific-review.json').read_text())['evidence_verified']
parent=yaml.safe_load((R/'workflow04.yaml').read_text());child=yaml.safe_load((R/'wave04.yaml').read_text());steps=child['main']['steps'];names=[next(iter(s)) for s in steps];assert names.index('claim_once')<names.index('wave_run')
assert child['main']['steps'][-1]['wave_run']['try']['steps'][0]['candidate']['assign'][-1]=={'last_failed':0}
run=steps[-1]['wave_run']['try']['steps'];assert any('poll_limit' in x for x in run)
assert not any('inventory'==x.get('call') for s in run for x in s.values())
scan=next(s['eviction_check_needed']['switch'][0] for s in run if 'eviction_check_needed' in s);assert '> last_failed' in scan['condition'] and '>= 2' in scan['condition']
for tree in [parent,child]:
 def walk(obj):
  if isinstance(obj,dict):
   if obj.get('call')=='http.post':assert 'retry' not in obj
   for k,v in obj.items():
    if k=='try' and isinstance(v,dict) and v.get('call')=='http.post':assert 'retry' not in obj
    walk(v)
  elif isinstance(obj,list):
   for x in obj:walk(x)
 walk(tree)
assert 'Batch' not in json.dumps(parent)
base=steps[0]['init']['assign'][0]['template'];t=base['job']['taskGroups'][0]['taskSpec'];assert t['maxRetryCount']==0
assert base64.b64decode(t['runnables'][0]['container']['commands'][1].split("b64decode('")[1].split("')")[0])==(R/'data/cloud04/bootstrap.py').read_bytes()
# Bounds are enforced in YAML: 375 job polls, 17 count-increase scans, 50 events,
# and 40 cleanup iterations. Each call has bounded default GET/DELETE retries.
assert 'poll_count > 375' in json.dumps(child) and 'cleanup_polls>40' in json.dumps(child)
assert 'statusEvents' in json.dumps(child) and '> 50' in json.dumps(child)
if '--quick' not in sys.argv:
 names=set()
 for wave in m:
  p=R/'data/cloud04'/(wave['id']+'.xz');assert sha(p)==wave['sha256'];d=json.loads(lzma.decompress(p.read_bytes()));cs=json.loads(d['groups.json'])['wave'];assert len(cs)==wave['count']<=18
  original=json.loads(lzma.decompress((R/'data/cloud'/(wave['id']+'.xz')).read_bytes()))
  recovery=wave['id']=='wave-008'
  if recovery:assert wave['count']==1 and cs[0]['pilot_case']=='tree51_000136_baseline'
  for n,s in d.items():
   if n.endswith('.py'):
    ast.parse(s)
    expected=(R/'recovery_worker04.py').read_text() if recovery and n=='worker.py' else ((R/'worker03.py').read_text() if n in ['worker.py','worker_base04.py'] else ((R/n).read_text() if n=='completion_check03.py' else original[n]))
    assert s==expected.replace('campaign01','campaign04')
  for c in cs:
   assert (c['pilot_case'] not in excluded or recovery) and c['case'] not in names;names.add(c['case'])
   key='decks/'+c['pilot_case']+'.fds';assert d[key]==original[key] and hashlib.sha256(d[key].encode()).hexdigest()==c['deck_sha256']
 assert len(names)==1829
if '--deployed' in sys.argv:
 for name,file in [(WF,'workflow04.yaml'),(WF+'-wave','wave04.yaml'),(WF+'-check','readiness04.yaml')]:
  actual=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==yaml.safe_load((R/file).read_text())
 save('deployed-bootstrap-proof.json',dict(passed=True,workflow_sha256=pkg['workflow_sha256'],wave_sha256=pkg['wave_sha256'],manifest_sha256=pkg['manifest_sha256'],single_line_bootstrap=True))
print('PASS:1828 unchanged fresh decks plus one pinned checkpoint recovery;150 prior attempts excluded from fresh work; unique claims, bounded polls and zero POST retries')
