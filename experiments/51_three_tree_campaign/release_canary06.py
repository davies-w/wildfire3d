"""Publish immutable admission gate only after independently collected canary evidence."""
from cloud06 import *
import requests
assert (P/'execution.json').exists() and not (P/'canary-approved.json').exists()
proof=json.loads((R/'data/completed06/wave-000000/proof.json').read_text());assert proof['passed'] and len(proof['cases'])==1
c=proof['cases'][0];assert c['case']=='tree51_000273_baseline' and c['passed'] and c['physical_time_s']>=180-1e-5 and c['archive_parts_verified']
assert json.loads((P/'collection-batch-wave-000000.json').read_text())['proof']['status']['state']=='SUCCEEDED'
children=gc('workflows','executions','list',WF+'-case','--location=us-central1');found=[]
for e in children:
 s=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-case','--location=us-central1');a=json.loads(s.get('argument','{}'))
 if a.get('dry_run'):continue
 if a.get('index')==0:
  assert s['state']=='SUCCEEDED';v=json.loads(s['result']);assert v['passed'] and v['cleanup_verified'];found.append(s)
assert len(found)==1;save('canary-child-proof.json',found[0])
for group in [('compute','instances','list'),('compute','disks','list')]:assert not gc(*group,'--filter=labels.trial_id=t51r06-c0')
assert not gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=t51r06-c0')
gate=dict(passed=True,case=c['case'],archive_verified=True,batch_succeeded=True,cleanup_verified=True,proof_sha256=sha(R/'data/completed06/wave-000000/proof.json'),time=time.time())
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
r=requests.post('https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',params={'uploadType':'media','name':PREFIX+'control/canary-approved.json','ifGenerationMatch':0},headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},data=json.dumps(gate),timeout=60);r.raise_for_status();save('canary-approved.json',dict(gate=gate,object=r.json()));print('Independent canary verified; rolling slots released')
