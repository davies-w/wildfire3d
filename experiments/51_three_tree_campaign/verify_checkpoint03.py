"""Independently verify the preserved preemption checkpoint; no solver or cloud mutation."""
from cloud03 import *
import requests,base64,io,tarfile
prefix=PREFIX+'wave-008/tree51_000136_baseline/checkpoints/000/'
items={x['name']:x for x in json.loads((P/'terminal-objects.json').read_text())}
auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()}
def read(name):
 v=items[prefix+name]
 r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=120);r.raise_for_status();assert len(r.content)==int(v['size']) and base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash'];return r.content
manifest=json.loads(read('archive-manifest.json'));verified=json.loads(read('verified.json'))
assert manifest['complete'] and len(manifest['parts'])==1
part=manifest['parts'][0];data=read(part['name']);assert hashlib.sha256(data).hexdigest()==part['sha256']
expected={x['name']:x for x in verified['files']};found={}
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
 for m in tf:
  if not m.isfile():continue
  assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  name=Path(m.name).name
  if name not in expected:continue
  b=tf.extractfile(m).read();e=expected[name];assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'];assert name not in found;found[name]=e['sha256']
assert set(found)==set(expected)
assert any(n.endswith('.restart') for n in found) and verified['step']==1800 and verified['physical_time']==121.56627
save('checkpoint-inner-verification.json',dict(passed=True,case='tree51_000136_baseline',step=verified['step'],physical_time=verified['physical_time'],files=found,archive_sha256=part['sha256'],limitation='Archive and all declared file hashes verified; a cloud restore and strictly advancing first step remain required.'))
print('Checkpoint inner hashes PASS',len(found),'files at',verified['physical_time'])
