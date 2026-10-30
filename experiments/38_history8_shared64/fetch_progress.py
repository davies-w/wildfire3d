"""Fetch completed epoch scores only, with pinned generations/MD5 and SHA provenance."""
from pathlib import Path
import argparse,json,sys,subprocess,urllib.request,urllib.parse,hashlib,base64,re
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import G,BUCKET
p=argparse.ArgumentParser();p.add_argument('attempt',choices=['03','04','05']);a=p.parse_args();prefix='history38/training'+a.attempt+'/'
dest=R/('data/progress'+a.attempt);dest.mkdir(exist_ok=True)
token=subprocess.run([G,'auth','print-access-token'],capture_output=True,text=True,check=True).stdout.strip()
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=90)
base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o';items={};page=None
while True:
 q={'prefix':prefix,'maxResults':1000}
 if page:q['pageToken']=page
 with get(base+'?'+urllib.parse.urlencode(q)) as f:x=json.load(f)
 items.update({v['name'][len(prefix):]:v for v in x.get('items',[])})
 page=x.get('nextPageToken')
 if not page:break
proof={}
for name,meta in sorted(items.items()):
 if not re.fullmatch(r'fold00-epoch\d+\.json',name):continue
 checkpoint=name[:-5]+'.pt'
 if checkpoint not in items:continue
 path=dest/name
 if path.exists():blob=path.read_bytes()
 else:
  with get(base+'/'+urllib.parse.quote(meta['name'],safe='')+'?'+urllib.parse.urlencode({'alt':'media','generation':meta['generation']})) as f:blob=f.read()
 assert len(blob)==int(meta['size']) and base64.b64encode(hashlib.md5(blob).digest()).decode()==meta['md5Hash']
 v=json.loads(blob);assert v['epoch']==int(re.search(r'epoch(\d+)',name)[1]);assert 'train'in v and 'validation'in v
 if not path.exists():path.write_bytes(blob)
 proof[name]={'metadata':meta,'sha256':hashlib.sha256(blob).hexdigest(),'checkpoint_metadata':items[checkpoint]}
(R/('results'+a.attempt)/'progress-verified.json').write_text(json.dumps({'source_prefix':prefix,'scores':proof,'test_outcomes_read':False},indent=2)+'\n')
print(json.dumps({'attempt':a.attempt,'verified_epochs':len(proof),'latest_epoch':max([json.loads((dest/n).read_text())['epoch'] for n in proof],default=None)}))
