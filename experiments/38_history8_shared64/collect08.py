"""Read-only terminal collection with immutable generations, hashes and selection barrier."""
import base64,concurrent.futures,fcntl,hashlib,json,shutil,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import G,BUCKET,gc
def read(p):return json.loads((R/p).read_text())
def save(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n')
PREFIX='history38/training08/'
TAG='training08'
rotation=0
def main():
 with (R/'data/pair-sequence-collection.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  e=read('results08/execution.json')['name'].split('/')
  status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1')
  save(f'results/{TAG}-terminal-status.json',status)
  if status['state'] in ['ACTIVE','QUEUED']:print('TRAINING_ACTIVE; no collection');return
  inv={k:gc(*v,'--filter=labels.trial_id=gpu38-history08') for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
  save(f'results/{TAG}-cleanup.json',inv);assert not any(inv.values()),inv
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
  root=R/f'data/{TAG}-results';root.mkdir(exist_ok=True)
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
  job_status='job-status.json'
  fetch(job_status);job=json.loads((root/job_status).read_text())
  assert job['status']['state']=='SUCCEEDED','Diagnose terminal failure; preserve checkpoint, never resubmit blindly'
  fetch('complete.json');complete=json.loads((root/'complete.json').read_text());assert complete['success'] and complete['folds']==1
  fetch('optimizer-resume-check.json');assert json.loads((root/'optimizer-resume-check.json').read_text())['passed']
  fetch('manifest.json');manifest=json.loads((root/'manifest.json').read_text())
  size=sum(int(objects[n]['size']) for n in manifest)
  # Include all preserved earlier model inventories and original raw-transfer envelope.
  sys.path.insert(0,str(R.parent/'36_tree_density/model_evaluation'))
  from canonical_transfer_guard03 import check_transfer_bound
  package=read('results08/package.json')
  prior=R.parent/'37_integral_objective'
  extra_inputs=sum(json.loads((prior/p).read_text())['input_bytes'] for p in ['results/package.json','results03/package.json','results03/package.json','results04/package.json','results05/package.json','results06/package.json'])
  prior_output=sum(json.loads((prior/'results'/f'{tag}-collected.json').read_text())['bytes'] for tag in ['training03','training04','training06'])
  extra_inputs+=json.loads((R/'results01/package.json').read_text())['input_bytes']
  prior_output+=sum(v['metadata']['size'] and int(v['metadata']['size']) for k,v in json.loads((R/'results01/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  extra_inputs+=json.loads((R/'results02/package.json').read_text())['input_bytes']
  prior_output+=sum(int(v['metadata']['size']) for k,v in json.loads((R/'results02/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  extra_inputs+=json.loads((R/'results03/package.json').read_text())['input_bytes']
  extra_inputs+=json.loads((R/'results04/package.json').read_text())['input_bytes']
  prior_output+=sum(int(v['metadata']['size']) for k,v in json.loads((R/'results04/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  extra_inputs+=json.loads((R/'results05/package.json').read_text())['input_bytes']
  prior_output+=sum(int(v['metadata']['size']) for k,v in json.loads((R/'results05/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  extra_inputs+=json.loads((R/'results06/package.json').read_text())['input_bytes']
  prior_output+=sum(int(v['metadata']['size']) for k,v in json.loads((R/'results06/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  extra_inputs+=json.loads((R/'results07/package.json').read_text())['input_bytes']
  prior_output+=sum(int(v['metadata']['size']) for k,v in json.loads((R/'results07/preemption-audit.json').read_text())['objects'].items() if k!='inputs.tar')
  # Oregon03 is terminal/closed: replace speculative allowance with measured immutable inventory.
  assert read('results03/race-closed.json')['passed']
  assert read('results03/race-cancellation-audit.json')['passed']
  prior03=[];cursor=None
  while True:
   query={'prefix':'history38/training03/','maxResults':1000}
   if cursor:query['pageToken']=cursor
   with get(base+'?'+urllib.parse.urlencode(query)) as response:page03=json.load(response)
   prior03.extend(page03.get('items',[]));cursor=page03.get('nextPageToken')
   if not cursor:break
  assert not any('fold00-epoch' in o['name'] for o in prior03)
  prior_output+=sum(int(o['size']) for o in prior03 if not o['name'].endswith('/inputs.tar'))
  save('results08/oregon03-terminal-inventory.json',{'objects':prior03,'terminal_closed':True})
  transfer=check_transfer_bound(package['input_bytes']+extra_inputs,size+prior_output,current_prefix=PREFIX)
  save('results/training08-transfer-bound.json',transfer)
  assert shutil.disk_usage(root).free>3*size+10*1024**3,'Insufficient archive/cache/mirror space'
  save(f'results/{TAG}-output-inventory.json',{'bytes':size,'objects':{n:objects[n] for n in manifest},'source_prefix':PREFIX})
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for n in pool.map(lambda n:fetch(n,manifest[n]),manifest):print('VERIFIED',n,flush=True)
  report=json.loads((root/'report.json').read_text());assert hashlib.sha256((root/'report.json').read_bytes()).hexdigest()==complete['report_sha256']
  assert report['success'] and len(report['folds'])==len(report['tests'])==1
  freeze=json.loads((root/'selection-freeze.json').read_text());assert freeze['test_not_evaluated_yet'] and len(freeze['selected'])==1
  barrier=objects['selection-freeze.json']['timeCreated']
  for i in range(1):
   fold=report['folds'][i];test=report['tests'][i];assert fold['fold']==test['fold']==i
   assert freeze['selected'][i]=={'fold':i,'epoch':fold['selected_epoch']}
   assert test['selected_epoch']==fold['selected_epoch']
   assert fold['rotation']==test['rotation']==rotation and fold['kind']==test['kind']=='gated'
   import numpy as np
   predictions=np.load(root/f'fold{i:02}-test-predictions.npz')
   expected=read('data/training08/schema.json')['rotations'][0]['test']
   assert predictions['case_indices'].tolist()==expected and len(expected)==len(set(expected)) and len({tuple(read('data/training08/schema.json')['cases'][j]['physical_key']) for j in expected})==204
   assert json.loads((root/f'fold{i:02}-checkpoint-replay.json').read_text())['optimizer_nonempty']
   assert objects[f'fold{i:02}-selected.pt']['timeCreated']<=barrier
   for epoch in range(1,fold['epochs']+1):assert f'fold{i:02}-epoch{epoch:03}.pt' in manifest
  test_names=[n for n in manifest if '-test' in n or '-horizon' in n]
  assert test_names and all(objects[n]['timeCreated']>=barrier for n in test_names)
  save(f'results/{TAG}-collected.json',{'passed':True,'rotation':rotation,'source_prefix':PREFIX,'test_histories':len(expected),'folds':1,'bytes':size,'objects_verified':len(manifest),'all_epoch_checkpoints_preserved':True,'all_selections_before_any_test_output':True,'cleanup_verified':True,'accuracy_analysis_pending':True})
if __name__=='__main__':main()
