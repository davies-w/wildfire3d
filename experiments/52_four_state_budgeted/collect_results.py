"""Collect only immutable scientific outputs; private cloud records stay private."""
from pathlib import Path
import json,subprocess,urllib.request,urllib.parse,hashlib,base64,re
R=Path(__file__).resolve().parent;G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud');BUCKET='tmrw-wildfire-20261015-trial';PREFIX='fourstate52/training01/'
def main():
 token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
 def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=180).read()
 objects=[];page=None
 while True:
  q={'prefix':PREFIX,'maxResults':1000}
  if page:q['pageToken']=page
  listing=json.loads(get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o?'+urllib.parse.urlencode(q)));objects+=listing.get('items',[]);page=listing.get('nextPageToken')
  if not page:break
 (R/'private/cloud-object-inventory.json').write_text(json.dumps(objects,indent=2)+'\n')
 allowed=re.compile(r'(?:fold00-[a-zA-Z0-9-]+\.(?:json|pt|npz)|(?:report|manifest|complete|selection-freeze|cuda-check|evaluation-cloud-check|transport-cloud-check|timing-check|optimizer-resume-check)\.json)$')
 out=R/'data/results';out.mkdir(exist_ok=True);verified=[]
 for obj in objects:
  name=obj['name'].removeprefix(PREFIX)
  if not allowed.fullmatch(name):continue
  p=out/name
  if not p.exists():
   b=get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(obj['name'],safe='')+'?alt=media&generation='+obj['generation'])
   assert len(b)==int(obj['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==obj['md5Hash'];p.write_bytes(b)
  assert base64.b64encode(hashlib.md5(p.read_bytes()).digest()).decode()==obj['md5Hash'],name
  verified.append(name)
 if (out/'manifest.json').exists():
  for n,h in json.loads((out/'manifest.json').read_text()).items():assert (out/n).exists() and hashlib.sha256((out/n).read_bytes()).hexdigest()==h,n
 complete=(out/'complete.json').exists()
 if complete:
  c=json.loads((out/'complete.json').read_text());assert c['success'] and c['report_sha256']==hashlib.sha256((out/'report.json').read_bytes()).hexdigest();assert json.loads((out/'selection-freeze.json').read_text())['test_not_evaluated_yet']
 (R/'private/collection.json').write_text(json.dumps(dict(files=verified,complete=complete,all_downloaded_bytes_md5_verified=True),indent=2)+'\n')
 print(json.dumps(dict(scientific_files=len(verified),complete=complete,epochs=sum(bool(re.fullmatch(r'fold00-epoch\d+\.json',n)) for n in verified))))
if __name__=='__main__':main()
