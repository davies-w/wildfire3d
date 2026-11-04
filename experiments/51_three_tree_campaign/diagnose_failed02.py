"""Verify failed-case final archive and extract only small private diagnostic logs."""
from cloud02 import *
import requests,base64,tarfile,io
case='tree51_000088_baseline';prefix=PREFIX+'wave-005/'+case+'/'
items={x['name']:x for x in json.loads((P/'terminal-objects.json').read_text())};record=next(x['proof'] for x in json.loads((P/'worker-proofs.json').read_text()) if x['name']==prefix+'completion.json');assert not record['passed'];parts=record['archive']['parts'];assert len(parts)==1
part=parts[0];v=items[prefix+part['name']];auth={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()}
r=requests.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},headers=auth,timeout=120);r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==part['sha256'] and base64.b64encode(hashlib.md5(r.content).digest()).decode()==v['md5Hash']
out=P/'failure-inspection';out.mkdir(exist_ok=True);names=[]
with tarfile.open(fileobj=io.BytesIO(r.content),mode='r:gz') as tf:
 for m in tf:
  if not m.isfile():continue
  names.append(dict(name=m.name,bytes=m.size))
  if m.size>8*1024**2 or '..' in Path(m.name).parts or Path(m.name).is_absolute():continue
  if m.name.endswith(('.log','.out','.json')):
   dest=out/m.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tf.extractfile(m).read())
save('failure-archive-proof.json',dict(passed=True,case=case,generation=v['generation'],sha256=part['sha256'],members=names));print('Verified failed final archive; private small diagnostics extracted')
