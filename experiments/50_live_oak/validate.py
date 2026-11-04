"""Validate every declared deck change, frozen bootstrap and controller limits offline."""
from cloud import *
import re,yaml,lzma,base64,ast,sys
from decimal import Decimal
OLD=R.parent/'48_two_tree_design';p=json.loads((P/'package.json').read_text());assert sha(R/'data/cloud/input.xz')==p['input_sha256'] and sha(R/'workflow.yaml')==p['workflow_sha256']
cases=json.loads((R/'data/pilot/cases.json').read_text());assert len(cases)==10
payload=json.loads(lzma.decompress((R/'data/cloud/input.xz').read_bytes()))
audit=json.loads((R/'data/pilot/validation.json').read_text());assert audit['passed'] and len(audit['cases'])==10
for c in cases:
 text=payload['decks/'+c['pilot_case']+'.fds'];assert hashlib.sha256(text.encode()).hexdigest()==c['deck_sha256']
 assert c['type_id']==2 and c['domain'][:2]==[29,20] and c['dx']==.5 and c['variant']=='baseline'
 assert 'T_END=180' in text and 'DT_SL3D=36.' in text
for n,s in payload.items():
 if n.endswith('.py'):ast.parse(s)
w=yaml.safe_load((R/'workflow.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates'];assert len(cs)==2
for c,n in zip(cs,[2,8]):
 t=c['job']['taskGroups'][0];assert t['taskCount']==str(n) and t['parallelism']==str(n) and t['taskSpec']['maxRetryCount']==0 and t['taskSpec']['maxRunDuration']=='10800s'
 code=t['taskSpec']['runnables'][0]['container']['commands'][1];assert '\n' not in code;ast.parse(code);decoded=base64.b64decode(re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)",code)[1]).decode();assert decoded==(R/'data/cloud/bootstrap.py').read_text()
proof=dict(passed=True,cases=10,type_id=2,offline_geometry_mass_checks=True,input_sha256=p['input_sha256'],actual_solver_checks_pending=True)
(R/'data/cloud/validation.json').write_text(json.dumps(proof,indent=2)+'\n');print('Offline10-case oak validation passed')
if '--deployed' in sys.argv:
 actual=yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents']);assert actual==w;save('deployed-bootstrap-proof.json',dict(passed=True,exact_source_and_bootstrap=True))
