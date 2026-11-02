"""Preserve a user-stopped run; raw cloud provenance remains private."""
from pathlib import Path
import sys,json,subprocess,urllib.parse,hashlib,base64,requests,concurrent.futures,os,re
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'));from cloud import gc,G,BUCKET
O=R/'results02';D=R/'data/stopped-pool02';D.mkdir(exist_ok=True)
p=json.loads((O/'package.json').read_text());assert (O/'before-user-stop.json').exists()
e=json.loads((O/'execution.json').read_text())['name'];state=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1');assert state['state'] in ['FAILED','SUCCEEDED','CANCELLED'],state['state']
for c in p['candidates']:
 for args in [('batch','jobs','list','--location='+c['region']),('compute','instances','list'),('compute','disks','list')]:assert not gc(*args,'--filter=labels.trial_id='+c['label'])
headers={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()};base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o';items=[];page=None
while True:
 params=dict(prefix=p['prefix'],maxResults=1000)
 if page:params['pageToken']=page
 q=requests.get(base,headers=headers,params=params,timeout=60);q.raise_for_status();x=q.json();items+=x.get('items',[]);page=x.get('nextPageToken')
 if not page:break
assert sum(int(m['size']) for m in items)<2*1024**3
assert __import__('shutil').disk_usage(R).free>sum(int(m['size']) for m in items)+2*1024**3
def get(m):
 n=m['name'][len(p['prefix']):];dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True)
 if n=='inputs.tar' and not dest.exists():os.link(R/'data/training02/inputs.tar',dest)
 if not dest.exists():
  q=requests.get(base+'/'+urllib.parse.quote(m['name'],safe=''),headers=headers,params=dict(alt='media',generation=m['generation']),timeout=90);q.raise_for_status();tmp=dest.with_suffix(dest.suffix+'.download');tmp.write_bytes(q.content);tmp.replace(dest)
 b=dest.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'];return n,dict(metadata=m,sha256=hashlib.sha256(b).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:proof=dict(pool.map(get,items))
science=R/'data/stopped-training';science.mkdir(exist_ok=True)
for n in proof:
 if re.fullmatch(r'or/fold00-(epoch\d+\.(pt|json)|baseline.json|checkpoint-replay.json)',n):
  dst=science/Path(n).name
  if not dst.exists():os.link(D/n,dst)
import torch
last=max(science.glob('fold00-epoch*.pt'));ck=torch.load(last,map_location='cpu',weights_only=False);assert ck['optimizer']['state'] and ck['rng'] and ck['history'];epochs=ck['epoch']
assert all((science/f'fold00-epoch{i:03}.pt').exists() for i in range(1,epochs+1))
(O/'stopped-archive.json').write_text(json.dumps(dict(passed=True,objects=proof,completed_epoch=epochs,all_checkpoint_states_preserved=True),indent=2)+'\n')
print('Archived',len(proof),'objects; all checkpoints through',epochs,flush=True)
