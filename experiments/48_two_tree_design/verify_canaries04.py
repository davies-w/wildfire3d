"""Verify archived successful canaries and export only scientific solver files."""
from cloud48_04 import *
import io,tarfile,csv
assert json.loads((P/'failure04-archive.json').read_text())['passed']
out=R/'data/canaries04';out.mkdir(exist_ok=True);proof=[]
for folder in sorted((P/'failed-pilot04/canary').iterdir()):
 if not folder.is_dir():continue
 c=json.loads((folder/'completion.json').read_text());assert c['passed'] and c['archive']['complete']
 blobs=[]
 for part in c['archive']['parts']:
  b=(folder/part['name']).read_bytes();assert hashlib.sha256(b).hexdigest()==part['sha256'];blobs.append(b)
 with tarfile.open(fileobj=io.BytesIO(b''.join(blobs)),mode='r:gz') as t:
  result=json.load(t.extractfile('evidence/result.json'));assert result['passed'] and result['physical_time']>=180-1e-5
  files=json.load(t.extractfile('evidence/files.json'));assert files['passed']
  for m in t:
   if not m.isfile():continue
   path=Path(m.name);assert '..' not in path.parts
   if path.suffix not in {'.fds','.csv','.restart','.sf','.prt5','.smv','.xyz','.sz','.bnd'}:continue
   if 'solve' not in path.parts:continue
   dest=out/folder.name/Path(*path.parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True)
   dest.write_bytes(t.extractfile(m).read())
 proof.append(dict(case=folder.name,passed=True,physical_time_s=result['physical_time'],deck_sha256=c['deck_sha256'],startup_passed=json.loads((folder/'startup.json').read_text())['passed']))
assert len(proof)==4
(out/'proof.json').write_text(json.dumps(dict(passed=True,cases=proof),indent=2)+'\n')
print(json.dumps(proof,indent=2))
