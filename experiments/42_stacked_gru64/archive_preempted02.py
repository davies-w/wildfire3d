"""Archive all pool02 objects and verify the last completed full checkpoint."""
from pathlib import Path
import sys,json,subprocess,requests,hashlib,base64,concurrent.futures,shutil,torch
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'));from cloud import gc,G,BUCKET
O=R/'results02';D=R/'data/preempted02';D.mkdir(exist_ok=True)
p=json.loads((O/'package.json').read_text());e=json.loads((O/'execution.json').read_text())['name'];state=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1');assert state['state']=='SUCCEEDED' and json.loads(state['result'])['batch_state']=='FAILED'
job=json.loads((O/'terminal-job.json').read_text());assert job['status']['state']=='FAILED' and 'Spot VM preemption with exit code 50001' in json.dumps(job)
headers={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()};base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o';q=requests.get(base,headers=headers,params=dict(prefix=p['prefix'],maxResults=1000),timeout=30);q.raise_for_status();ls=q.json();assert not ls.get('nextPageToken');assert shutil.disk_usage(D).free>sum(int(m['size']) for m in ls['items'])*3+10*1024**3

def fetch(m):
 n=m['name'][len(p['prefix']):];f=D/n;f.parent.mkdir(parents=True,exist_ok=True)
 if not f.exists():
  if n=='inputs.tar':shutil.copy2(R/'data/training02/inputs.tar',f)
  else:
   q=requests.get(base+'/'+requests.utils.quote(m['name'],safe=''),headers=headers,params=dict(alt='media',generation=m['generation']),timeout=90);q.raise_for_status();f.write_bytes(q.content)
 b=f.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'];return n,dict(metadata=m,sha256=hashlib.sha256(b).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:proof=dict(pool.map(fetch,ls['items']))
assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256'];checkpoint='ia/fold00-epoch030.pt';ck=torch.load(D/checkpoint,map_location='cpu',weights_only=False);assert ck['epoch']==30 and ck['optimizer']['state'] and ck['rng'] and ck['schema_hash']==hashlib.sha256((R/'data/training02/schema.json').read_bytes()).hexdigest();assert len([x for x in ck['history'] if x['epoch']>0])==30
for epoch in range(1,31):assert f'ia/fold00-epoch{epoch:03}.pt' in proof and f'ia/fold00-epoch{epoch:03}.json' in proof
assert not any('epoch031' in n for n in proof);assert json.loads((O/'startup-audit-ia.json').read_text())['passed']
(O/'preemption-audit.json').write_text(json.dumps(dict(passed=True,latest_epoch=30,next_epoch=31,checkpoint=checkpoint,checkpoint_sha256=proof[checkpoint]['sha256'],all_seven_startup_proofs_passed=True,objects=proof),indent=2)+'\n');print('Archived',len(proof),'objects; verified full checkpoint30',proof[checkpoint]['sha256'])
