"""Validate every declared deck change, frozen bootstrap and controller limits offline."""
from cloud import *
import re,yaml,lzma,base64,ast,sys
from decimal import Decimal
OLD=R.parent/'48_two_tree_design';p=json.loads((P/'package.json').read_text());assert sha(R/'data/cloud/input.xz')==p['input_sha256'] and sha(R/'workflow.yaml')==p['workflow_sha256']
cases=json.loads((R/'data/cases.json').read_text());old={c['pilot_case']:c for c in json.loads((OLD/'data/pilot/cases.json').read_text())};payload=json.loads(lzma.decompress((R/'data/cloud/input.xz').read_bytes()))
for c in cases:
 a=old[c['original_case']];original=(OLD/'data/pilot/decks'/(a['pilot_case']+'.fds')).read_text();new=payload['decks/'+c['pilot_case']+'.fds'];assert hashlib.sha256(new.encode()).hexdigest()==c['deck_sha256'];dy=8-a['domain'][1]/2
 def norm(s,shift):
  s=re.sub(r"CHID='[^']+'", "CHID='CASE'",s);s=re.sub(r"TITLE='[^']+'","TITLE='TITLE'",s);s=re.sub(r'IJK=\d+,\d+,\d+','IJK=GRID',s);s=re.sub(r'XB=0,\d+,0,\d+,0,\d+','XB=DOMAIN',s);s=re.sub(r'PBY=[\d.]+','PBY=CENTER',s)
  def xyz(m):
   v=[Decimal(x) for x in m[1].split(',')];v[1]-=Decimal(str(shift));return 'XYZ='+','.join(f'{x:.8f}' for x in v)
  return re.sub(r'XYZ=([-+\d.eE]+,[-+\d.eE]+,[-+\d.eE]+)',xyz,s)
 assert norm(original,0)==norm(new,dy),'Undeclared physics edit '+c['pilot_case']
 assert c['expected_wet_mass_kg']==a['expected_wet_mass_kg'] and c['domain'][:2]==[24,16] and c['dx']==.5
for n,s in payload.items():
 if n.endswith('.py'):ast.parse(s)
w=yaml.safe_load((R/'workflow.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates'];assert len(cs)==2
for c,n in zip(cs,[4,18]):
 t=c['job']['taskGroups'][0];assert t['taskCount']==str(n) and t['parallelism']==str(n) and t['taskSpec']['maxRetryCount']==0 and t['taskSpec']['maxRunDuration']=='10800s'
 code=t['taskSpec']['runnables'][0]['container']['commands'][1];assert '\n' not in code;ast.parse(code);decoded=base64.b64decode(re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)",code)[1]).decode();assert decoded==(R/'data/cloud/bootstrap.py').read_text()
proof=dict(passed=True,cases=22,only_domain_translation_identifier_changes=True,same_particle_fuel_and_ignition_parameters=True,input_sha256=p['input_sha256'],actual_solver_checks_pending=True)
(R/'data/cloud/validation.json').write_text(json.dumps(proof,indent=2)+'\n');print('Offline22-case validation passed')
if '--deployed' in sys.argv:
 actual=yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents']);assert actual==w;save('deployed-bootstrap-proof.json',dict(passed=True,exact_source_and_bootstrap=True))
