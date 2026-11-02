"""Offline integrity checks for the immutable launch package; never starts a solver."""
from cloud48 import *
import yaml,lzma,ast,io,tarfile,tempfile
pkg=json.loads((P/'package.json').read_text());assert pkg['input_sha256']==sha(R/'data/cloud/input.xz');assert pkg['workflow_sha256']==sha(R/'pilot01.yaml')
payload=json.loads(lzma.decompress((R/'data/cloud/input.xz').read_bytes()));groups=json.loads(payload['groups.json']);assert [len(groups[k]) for k in ['canary','bulk']]==[4,20]
allcases=groups['canary']+groups['bulk'];assert len({c['pilot_case'] for c in allcases})==24
for c in allcases:assert hashlib.sha256(payload['decks/'+c['pilot_case']+'.fds'].encode()).hexdigest()==c['deck_sha256']
assert {(c['type_id'],c['ignition']['mode']) for c in groups['canary']}=={(1,'base'),(1,'crown'),(3,'base'),(3,'crown')}
w=yaml.safe_load((R/'pilot01.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates']
for c,n in zip(cs,[4,20]):
 t=c['job']['taskGroups'][0];assert int(t['taskCount'])==n and int(t['parallelism'])==n and t['taskCountPerNode']=='1';assert t['taskSpec']['maxRetryCount']==0;assert c['job']['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT';assert c['job']['allocationPolicy']['instances'][0]['policy']['machineType'] in ['c3-standard-4','c3-highmem-4']
for f in R.glob('*.py'):ast.parse(f.read_text())
import pilot_worker as worker
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'checkpoint.restart').write_bytes(b'offline archive roundtrip');parts={};m=worker.archive(p,lambda n,b:parts.__setitem__(n,b));data=b''.join(parts[v['name']] for v in m['parts']);t=tarfile.open(fileobj=io.BytesIO(data));assert t.extractfile('evidence/checkpoint.restart').read()==b'offline archive roundtrip';assert all(hashlib.sha256(parts[v['name']]).hexdigest()==v['sha256'] for v in m['parts'])
proof=dict(passed=True,cases=24,canaries=4,bulk_parallelism=20,input_sha256=pkg['input_sha256'],scope='Offline package hashes, array mapping, Spot-only/no-retry policy, Python syntax and archive reconstruction. Cloud solver proofs pending.')
(R/'data/cloud/validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
(R/'launch-record.json').write_text(json.dumps(pkg,indent=2)+'\n')
