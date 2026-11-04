"""Validate frozen package and optionally exact deployed workflow bytes; no solve."""
from cloud import *
import ast,base64,lzma,sys,yaml
pkg=json.loads((P/'package.json').read_text());assert pkg['new_cases']==1978 and pkg['reused']==22 and pkg['cases']==2000
assert sha(R/'data/cloud/manifest.json')==pkg['manifest_sha256'] and sha(R/'workflow.yaml')==pkg['workflow_sha256']
m=json.loads((R/'data/cloud/manifest.json').read_text());assert m[0]['count']==6 and sum(w['count'] for w in m)==1978
names=set()
for wave in m:
 p=R/'data/cloud'/(wave['id']+'.xz');assert sha(p)==wave['sha256'];d=json.loads(lzma.decompress(p.read_bytes()));cs=json.loads(d['groups.json'])['wave'];assert len(cs)==wave['count']<=18
 assert 'checkpoint_control.py' in d and 'min(480,' in d['worker.py'] and 'checkpoint_control=control' in d['worker.py']
 for n,s in d.items():
  if n.endswith('.py'):ast.parse(s)
 for c in cs:
  assert c['reuse'] is None and c['case'] not in names;names.add(c['case'])
  assert hashlib.sha256(d['decks/'+c['pilot_case']+'.fds'].encode()).hexdigest()==c['deck_sha256']
assert len(names)==1978
w=yaml.safe_load((R/'workflow.yaml').read_text());assert 'adapt_checkpoints' in w
init=w['main']['steps'][0]['init']['assign'];base=next(x['template'] for x in init if 'template' in x)
t=base['job']['taskGroups'][0]['taskSpec'];assert t['maxRetryCount']==0
command=t['runnables'][0]['container']['commands'];assert command[0]=='-c' and len(command)==2
encoded=command[1].split("b64decode('")[1].split("')")[0];assert base64.b64decode(encoded)==(R/'data/cloud/bootstrap.py').read_bytes()
loop=w['main']['steps'][5]['campaign']['try']['steps'][1]['waves']['for']['steps'];assert list(loop[0])==['budget_admission']
assert next(x['account_wave']['assign'][0]['spent'] for x in loop if 'account_wave' in x).find('wave_started')>=0
if '--deployed' in sys.argv:
 actual=gc('workflows','describe',WF,'--location=us-central1');assert yaml.safe_load(actual['sourceContents'])==w
 save('deployed-bootstrap-proof.json',dict(passed=True,workflow_sha256=pkg['workflow_sha256'],manifest_sha256=pkg['manifest_sha256'],single_line_bootstrap=True))
print('Validated1978unique new cases,22reuse,zero retries,live checkpoint policy and budget gate')
