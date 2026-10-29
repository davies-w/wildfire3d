"""Fetch only startup proofs, pinning object generations and verifying MD5/SHA."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import G,BUCKET
PREFIX='integral37/training04/';D=R/'data/startup-audit04';D.mkdir(exist_ok=True)
token=subprocess.run([G,'auth','print-access-token'],check=True,capture_output=True,text=True).stdout.strip()
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=60)
proof={}
for name in ['timing-check.json','optimizer-resume-check.json','fold00-checkpoint-replay.json','cuda-check.json','evaluation-cloud-check.json','transport-cloud-check.json']:
 url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(PREFIX+name,safe='')
 with get(url) as f:meta=json.load(f)
 with get(url+'?'+urllib.parse.urlencode(dict(alt='media',generation=meta['generation']))) as f:blob=f.read()
 assert len(blob)==int(meta['size']) and base64.b64encode(hashlib.md5(blob).digest()).decode()==meta['md5Hash']
 obj=json.loads(blob);assert obj['passed'];(D/name).write_bytes(blob)
 proof[name]=dict(metadata=meta,sha256=hashlib.sha256(blob).hexdigest(),value=obj)
(R/'results04/startup-audit.json').write_text(json.dumps(dict(passed=True,source_prefix=PREFIX,proofs=proof),indent=2)+'\n')
print('Verified six startup proofs; no test outcomes read')
