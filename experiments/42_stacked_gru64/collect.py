"""Collect terminal pool02 scientific artifacts with pinned hashes and test barrier."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64,shutil,concurrent.futures
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET
O=R/'results02';D=R/'data/pool02-results';D.mkdir(exist_ok=True)
p=json.loads((O/'package.json').read_text());e=json.loads((O/'execution.json').read_text())['name'];state=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1')
assert state['state']=='SUCCEEDED';result=json.loads(state['result']);assert result['batch_state']=='SUCCEEDED' and result['cleanup_verified'];winner=result['winner'];prefix=p['prefix']+winner+'/'
cleanup={}
for c in p['candidates']:
 cleanup[c['id']]={k:gc(*v,'--filter=labels.trial_id='+c['label']) for k,v in dict(jobs=('batch','jobs','list','--location='+c['region']),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(cleanup[c['id']].values())
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=180)
base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o'
def listing(prefix):
 out=[];page=None
 while True:
  q=dict(prefix=prefix,maxResults=1000)
  if page:q['pageToken']=page
  with get(base+'?'+urllib.parse.urlencode(q)) as f:x=json.load(f)
  out+=x.get('items',[]);page=x.get('nextPageToken')
  if not page:return out
objects={x['name'][len(prefix):]:x for x in listing(prefix)}
def fetch(name,sha=None):
 assert Path(name).name==name
 m=objects[name];dest=D/name
 if not dest.exists():
  with get(base+'/'+urllib.parse.quote(m['name'],safe='')+'?'+urllib.parse.urlencode(dict(alt='media',generation=m['generation']))) as f:b=f.read()
  assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash']
  if sha:assert hashlib.sha256(b).hexdigest()==sha
  dest.write_bytes(b)
 b=dest.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash']
 if sha:assert hashlib.sha256(b).hexdigest()==sha
 return dict(metadata=m,sha256=hashlib.sha256(b).hexdigest())
status=max((n for n in objects if n.startswith('job-status.json.')),key=lambda n:objects[n]['timeCreated']);fetch(status);assert json.loads((D/status).read_text())['status']['state']=='SUCCEEDED';shutil.move(str(D/status),str(O/status))
fetch('complete.json');complete=json.loads((D/'complete.json').read_text());assert complete['success']
fetch('manifest.json');manifest=json.loads((D/'manifest.json').read_text());size=sum(int(objects[n]['size']) for n in manifest)
assert shutil.disk_usage(D).free>3*size+10*1024**3
# Account for all previous model transport across37/38 and this continuation.
all_objects=sum([listing(x) for x in ['integral37/','history38/','longwindow39/','dropout40/','dropout41/','stacked42/']],[])
input_bytes=sum(int(x['size']) for x in all_objects if x['name'].endswith('/inputs.tar'))
output_bytes=sum(int(x['size']) for x in all_objects if not x['name'].endswith('/inputs.tar'))
sys.path.insert(0,str(R.parent/'36_tree_density/model_evaluation'))
from canonical_transfer_guard03 import check_transfer_bound
transfer=check_transfer_bound(input_bytes,output_bytes,current_prefix=prefix)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:proof=dict(zip(manifest,pool.map(lambda n:fetch(n,manifest[n]),manifest)))
report=json.loads((D/'report.json').read_text());assert hashlib.sha256((D/'report.json').read_bytes()).hexdigest()==complete['report_sha256'];assert report['success'] and len(report['folds'])==len(report['tests'])==1
fold=report['folds'][0];test=report['tests'][0];freeze=json.loads((D/'selection-freeze.json').read_text());assert freeze['test_not_evaluated_yet'];assert freeze['selected']==[dict(fold=0,epoch=fold['selected_epoch'])];assert test['selected_epoch']==fold['selected_epoch']
barrier=objects['selection-freeze.json']['timeCreated'];assert objects['fold00-selected.pt']['timeCreated']<=barrier
assert all(objects[n]['timeCreated']>=barrier for n in manifest if '-test' in n or '-horizon' in n)
for epoch in range(1,fold['epochs']+1):assert f'fold00-epoch{epoch:03}.pt' in manifest
import numpy as np,torch
schema=json.loads((R/'data/training02/schema.json').read_text());ids=schema['rotations'][0]['test'];pred=np.load(D/'fold00-test-predictions.npz');assert pred['case_indices'].tolist()==ids and len(ids)==len(set(ids))==208 and len({tuple(schema['cases'][i]['physical_key']) for i in ids})==204
ck=torch.load(D/f"fold00-epoch{fold['selected_epoch']:03}.pt",map_location='cpu',weights_only=False);assert ck['epoch']==fold['selected_epoch'] and ck['optimizer']['state'] and ck['rng'];assert ck['schema_hash']==hashlib.sha256((R/'data/training02/schema.json').read_bytes()).hexdigest()
audit=dict(passed=True,winner=winner,controller=state,cleanup=cleanup,objects=proof,bytes=size,transfer=transfer,epochs=fold['epochs'],selected_epoch=fold['selected_epoch'],test_histories=208,test_configurations=204,selection_before_tests=True,all_checkpoints_preserved=True)
(O/'collected.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k not in ['controller','cleanup','objects','transfer']}))
