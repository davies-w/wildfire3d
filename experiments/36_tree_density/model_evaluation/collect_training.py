"""Read-only terminal collection with immutable generations, hashes and selection barrier."""
import base64,concurrent.futures,fcntl,hashlib,json,shutil,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
PREFIX='density36/model-training01/'
def main():
 with (R/'data/model-training-collection.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  e=read('results/model-training-execution.json')['name'].split('/')
  status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1')
  save('results/model-training-status.json',status)
  if status['state']=='ACTIVE':print('TRAINING_ACTIVE; no collection');return
  inv={k:gc(*v,'--filter=labels.trial_id=gpu36-training01') for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
  save('results/model-training-cleanup.json',inv);assert not any(inv.values()),inv
  token=subprocess.run([G,'auth','print-access-token'],check=True,capture_output=True,text=True).stdout.strip()
  def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=180)
  base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o';objects={};page=None
  while True:
   q={'prefix':PREFIX,'maxResults':1000}
   if page:q['pageToken']=page
   with get(base+'?'+urllib.parse.urlencode(q)) as response:listing=json.load(response)
   for item in listing.get('items',[]):objects[item['name'][len(PREFIX):]]=item
   page=listing.get('nextPageToken')
   if not page:break
  root=R/'data/model-training-results';root.mkdir(exist_ok=True)
  def fetch(name,sha=None):
   assert Path(name).name==name and name not in ('.','..'),name
   meta=objects[name];dest=root/name
   if not dest.exists():
    part=root/(name+'.partial');assert not part.exists(),'Diagnose preserved partial before retry: '+str(part)
    url=base+'/'+urllib.parse.quote(meta['name'],safe='')+'?'+urllib.parse.urlencode({'alt':'media','generation':meta['generation']})
    with get(url) as src,part.open('xb') as dst:shutil.copyfileobj(src,dst)
    check(part,meta,sha);part.rename(dest)
   check(dest,meta,sha)
   return name
  def check(path,meta,sha):
   h=hashlib.sha256();m=hashlib.md5();size=0
   with path.open('rb') as f:
    for block in iter(lambda:f.read(1024*1024),b''):h.update(block);m.update(block);size+=len(block)
   assert size==int(meta['size']) and base64.b64encode(m.digest()).decode()==meta['md5Hash'],path
   if sha:assert h.hexdigest()==sha,path
  fetch('job-status.json');job=json.loads((root/'job-status.json').read_text())
  assert job['status']['state']=='SUCCEEDED','Diagnose terminal failure; preserve checkpoint, never resubmit blindly'
  fetch('complete.json');complete=json.loads((root/'complete.json').read_text());assert complete['success'] and complete['folds']==10
  fetch('manifest.json');manifest=json.loads((root/'manifest.json').read_text())
  size=sum(int(objects[n]['size']) for n in manifest)
  assert size<30*1024**3,'Review transfer/storage allowance before collection'
  assert shutil.disk_usage(root).free>3*size+10*1024**3,'Insufficient archive/cache/mirror space'
  save('results/model-training-output-inventory.json',{'bytes':size,'objects':{n:objects[n] for n in manifest},'source_prefix':PREFIX})
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for n in pool.map(lambda n:fetch(n,manifest[n]),manifest):print('VERIFIED',n,flush=True)
  report=json.loads((root/'report.json').read_text());assert hashlib.sha256((root/'report.json').read_bytes()).hexdigest()==complete['report_sha256']
  assert report['success'] and len(report['folds'])==len(report['tests'])==10
  freeze=json.loads((root/'selection-freeze.json').read_text());assert freeze['test_not_evaluated_yet'] and len(freeze['selected'])==10
  barrier=objects['selection-freeze.json']['timeCreated']
  for i in range(10):
   fold=report['folds'][i];test=report['tests'][i];assert fold['fold']==test['fold']==i
   assert freeze['selected'][i]=={'fold':i,'epoch':fold['selected_epoch']}
   assert test['selected_epoch']==fold['selected_epoch']
   assert json.loads((root/f'fold{i:02}-checkpoint-replay.json').read_text())['optimizer_nonempty']
   assert objects[f'fold{i:02}-selected.pt']['timeCreated']<=barrier
   for epoch in range(1,fold['epochs']+1):assert f'fold{i:02}-epoch{epoch:03}.pt' in manifest
  test_names=[n for n in manifest if '-test' in n or '-horizon' in n]
  assert test_names and all(objects[n]['timeCreated']>=barrier for n in test_names)
  save('results/model-training-collected.json',{'passed':True,'folds':10,'bytes':size,'objects_verified':len(manifest),'all_epoch_checkpoints_preserved':True,'all_selections_before_any_test_output':True,'cleanup_verified':True,'accuracy_analysis_pending':True})
if __name__=='__main__':main()
