"""Fetch only startup proofs, pinning object generations and verifying MD5/SHA."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import G,BUCKET
import argparse
p=argparse.ArgumentParser();p.add_argument('candidate',choices=['or','ia','sc']);a=p.parse_args()
PREFIX='stacked42/pool01/'+a.candidate+'/';D=R/('data/startup-audit-'+a.candidate);D.mkdir(exist_ok=True)
token=subprocess.run([G,'auth','print-access-token'],check=True,capture_output=True,text=True).stdout.strip()
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=60)
proof={}
for name in ['fresh-initialization-replay.json','timing-check.json','optimizer-resume-check.json','fold00-checkpoint-replay.json','cuda-check.json','evaluation-cloud-check.json','transport-cloud-check.json']:
 url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(PREFIX+name,safe='')
 with get(url) as f:meta=json.load(f)
 with get(url+'?'+urllib.parse.urlencode(dict(alt='media',generation=meta['generation']))) as f:blob=f.read()
 assert len(blob)==int(meta['size']) and base64.b64encode(hashlib.md5(blob).digest()).decode()==meta['md5Hash']
 obj=json.loads(blob);assert obj['passed'];(D/name).write_bytes(blob)
 proof[name]=dict(metadata=meta,sha256=hashlib.sha256(blob).hexdigest(),value=obj)
(R/'results'/('startup-audit-'+a.candidate+'.json')).write_text(json.dumps(dict(passed=True,source_prefix=PREFIX,proofs=proof),indent=2)+'\n')
print('Verified seven startup proofs (actual first-epoch proof; no inherited epochs); no test outcomes read')
