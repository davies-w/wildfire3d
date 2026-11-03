"""Offline integrity checks for the immutable launch package; never starts a solver."""
from cloud48_04 import *
import yaml,lzma,ast,io,tarfile,tempfile
pkg=json.loads((P/'package.json').read_text());assert pkg['input_sha256']==sha(R/'data/cloud04/input.xz');assert pkg['workflow_sha256']==sha(R/'pilot04.yaml')
payload=json.loads(lzma.decompress((R/'data/cloud04/input.xz').read_bytes()));groups=json.loads(payload['groups.json']);assert [len(groups[k]) for k in ['canary','bulk']]==[4,20]
allcases=groups['canary']+groups['bulk'];assert len({c['pilot_case'] for c in allcases})==24
for c in allcases:assert hashlib.sha256(payload['decks/'+c['pilot_case']+'.fds'].encode()).hexdigest()==c['deck_sha256']
assert {(c['type_id'],c['ignition']['mode']) for c in groups['canary']}=={(1,'base'),(1,'crown'),(3,'base'),(3,'crown')}
w=yaml.safe_load((R/'pilot04.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates']
for c,n in zip(cs,[4,20]):
 t=c['job']['taskGroups'][0];assert int(t['taskCount'])==n and int(t['parallelism'])==n and t['taskCountPerNode']=='1';assert t['taskSpec']['maxRetryCount']==0;assert c['job']['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT';assert c['job']['allocationPolicy']['instances'][0]['policy']['machineType'] in ['c3-standard-4','c3-highmem-4']
for f in R.glob('*.py'):ast.parse(f.read_text())
import pilot_worker04 as worker
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'checkpoint.restart').write_bytes(b'offline archive roundtrip');parts={};m=worker.archive(p,lambda n,b:parts.__setitem__(n,b));data=b''.join(parts[v['name']] for v in m['parts']);t=tarfile.open(fileobj=io.BytesIO(data));assert t.extractfile('evidence/checkpoint.restart').read()==b'offline archive roundtrip';assert all(hashlib.sha256(parts[v['name']]).hexdigest()==v['sha256'] for v in m['parts'])
proof=dict(passed=True,cases=24,canaries=4,bulk_parallelism=20,input_sha256=pkg['input_sha256'],scope='Offline package hashes, array mapping, Spot-only/no-retry policy, Python syntax and archive reconstruction. Cloud solver proofs pending.')
(R/'data/cloud04/validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
(R/'launch-record04.json').write_text(json.dumps(pkg,indent=2)+'\n')
# Inspect exactly what the deployed workflow will pass to Python, not only local source.
import base64,re
actual=yaml.safe_load(gc('workflows','describe',WF,'--location=us-central1')['sourceContents'])
for c in actual['main']['steps'][0]['init']['assign'][0]['candidates']:
 command=c['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands'][1]
 assert '\n' not in command and '\\' not in command
 ast.parse(command)
 encoded=re.search(r"b64decode\('([A-Za-z0-9+/=]+)'\)",command)[1]
 decoded=base64.b64decode(encoded).decode();assert decoded==(R/'data/cloud04/bootstrap.py').read_text();ast.parse(decoded)
save('deployed-bootstrap-proof.json',dict(passed=True,source='Deployed Workflows sourceContents',single_line=True,decoded_sha256=hashlib.sha256(decoded.encode()).hexdigest()))
print('Deployed bootstrap roundtrip passed')
