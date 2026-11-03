"""Check exact recovery cases, bytes and deployment transport; never run a solver."""
from cloud48_07 import *
import yaml,lzma,ast,base64,re,sys
pkg=json.loads((P/'package.json').read_text());assert sha(R/'data/cloud07/input.xz')==pkg['input_sha256'];assert sha(R/'pilot07.yaml')==pkg['workflow_sha256']
payload=json.loads(lzma.decompress((R/'data/cloud07/input.xz').read_bytes()));cases=json.loads(payload['groups.json'])['bulk'];plans=json.loads(payload['recovery.json']);assert len(cases)==1 and set(plans)==set(pkg['case_ids'])
for c in cases:
 n=c['pilot_case'];assert '_fine' not in n;assert hashlib.sha256(payload['decks/'+n+'.fds'].encode()).hexdigest()==c['deck_sha256'];assert plans[n]['saved_step']>0
w=yaml.safe_load((R/'pilot07.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates'];assert len(cs)==1;t=cs[0]['job']['taskGroups'][0];assert t['taskCount']=='1' and t['parallelism']=='1' and t['taskSpec']['maxRetryCount']==0
assert cs[0]['job']['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT'
for n,s in payload.items():
 if n.endswith('.py'):ast.parse(s)
def check(w):
 for c in w['main']['steps'][0]['init']['assign'][0]['candidates']:
  command=c['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands'][1];assert '\n' not in command and '\\' not in command;ast.parse(command)
  decoded=base64.b64decode(re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)",command)[1]).decode();assert decoded==(R/'data/cloud07/bootstrap.py').read_text();ast.parse(decoded)
check(w)
proof=dict(passed=True,cases=1,continuation_only=True,completed_and_fine_excluded=True,input_sha256=pkg['input_sha256'],scope='Offline hashes, unique cases, checkpoint mapping and exact bootstrap decoding; cloud continuation pending')
(R/'data/cloud07/validation.json').write_text(json.dumps(proof,indent=2));print(proof)
if '--deployed' in sys.argv:
 actual=yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents']);assert actual==w;check(actual);save('deployed-bootstrap-proof.json',dict(passed=True,exact_deployed_source=True))
