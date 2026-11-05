"""Audit stopped indices, then prepare a one-time continuation at never-submitted index19."""
from cloud07 import *
import yaml,requests,math
assert not (P/'continuation-submission-intent.json').exists()
s=json.loads((P/'status.json').read_text());assert s['controller']['state']=='SUCCEEDED' and not s['jobs'] and not s['vms']
children=json.loads((P/'terminal-children-review.json').read_text());assert len(children)==19 and all(x['state'] in ['SUCCEEDED','FAILED'] for x in children)
passed={json.loads(x['argument'])['index'] for x in children if x['state']=='SUCCEEDED'};assert passed==set(range(19))-{9,15}
proofs=[json.loads(x.read_text()) for x in (R/'data/completed07').glob('wave-*/proof.json')];assert len(proofs)==17 and all(x['passed'] for x in proofs)
audit=json.loads((P/'interim-allocation-summary.json').read_text());assert audit['passed'] and audit['pairs']==17
empty={k:gc(*args,'--filter=name~t51r07') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(empty.values())
old=json.loads(s['controller']['result'])['state'];assert old['cursor']==19 and old['epoch']==2
state=dict(old);state.update(active={},spent=math.ceil(audit['compute_upper_usd']*1000000)+2*525000,started=17,completed=485,interrupted=2,stopped=False,audit_required=False)
# Failed submissions retain full conservative charges; they are excluded from this continuation.
payload=dict(state=state,prior_execution=s['controller']['name'],excluded_pending_review=[9,15],verified_successes=17,failed_reservations_retained=True)
save('continuation-state.json',payload)
parent=yaml.safe_load((R/'rolling07-parent.yaml').read_text());steps=parent['main']['steps'];steps[:]=[x for x in steps if next(iter(x)) not in ['initial_policy','inherited_policy']]
for x in steps:
 if 'owner_claim' in x:x['owner_claim']['args']['query']['name']='${"tree51/t51r07/continuation-1-claim.json"}'
 if 'init' in x:x['init']['assign']=[{'s':'${resume.body.state}'},{'polls':0},{'start':'${sys.now()}'}]
pos=next(i for i,x in enumerate(steps) if 'owner_claim' in x);steps.insert(pos,{'read_resume':{'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/tree51%2Ft51r07%2Fcontrol%2Fcontinuation-1.json','auth':{'type':'OAuth2'},'query':{'alt':'media'}},'result':'resume'}})
(R/'rolling07-resume1.yaml').write_text(yaml.safe_dump(parent,sort_keys=False))
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();r=requests.post('https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',params={'uploadType':'media','name':PREFIX+'control/continuation-1.json','ifGenerationMatch':0},headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},data=json.dumps(payload),timeout=60);r.raise_for_status();save('continuation-state-object.json',r.json())
gc('workflows','deploy',WF+'-resume1','--location=us-central1','--source='+str(R/'rolling07-resume1.yaml'),'--service-account=fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com');a=gc('workflows','describe',WF+'-resume1','--location=us-central1');assert yaml.safe_load(a['sourceContents'])==parent;save('continuous-deployed-parent.json',dict(passed=True,revision=a['revisionId'],sha256=sha(R/'rolling07-resume1.yaml')))
print('Continuation prepared at cursor19, no jobs submitted')
