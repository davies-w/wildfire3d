"""Read-only collection of one bounded pilot; no automatic retries or submissions."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys,json,base64,hashlib,shutil,subprocess,urllib.request,urllib.parse,fcntl,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
PREFIX='density36/canonical-pilot02/';LABEL='gpu36-canonical02'
def main():
 with (R/'data/canonical-pilot02-collect.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  e=read('results/canonical-pilot02-execution.json')['name'].split('/');status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');save('results/canonical-pilot02-status.json',status)
  inv={k:gc(*cmd,'--filter=labels.trial_id='+LABEL) for k,cmd in {'jobs':('batch','jobs','list','--location=us-east4'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
  if status['state']=='ACTIVE':
   progress={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workflow_state':status['state'],'jobs':[dict(name=j['name'],state=j['status']['state'],runDuration=j['status'].get('runDuration')) for j in inv['jobs']],'instances':[dict(name=v['name'],status=v['status']) for v in inv['instances']]};save('results/canonical-pilot02-progress.json',progress);print(json.dumps(progress));return
  save('results/canonical-pilot02-cleanup.json',inv)
  if any(inv.values()):print('TERMINAL_CLEANUP_PENDING; do not restart');return
  token=subprocess.run([G,'auth','print-access-token'],check=True,text=True,capture_output=True).stdout.strip()
  def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=180)
  base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o';objects={};page=None
  while True:
   q={'prefix':PREFIX,'maxResults':1000}
   if page:q['pageToken']=page
   with get(base+'?'+urllib.parse.urlencode(q)) as f:listing=json.load(f)
   for item in listing.get('items',[]):objects[item['name'][len(PREFIX):]]=item
   page=listing.get('nextPageToken')
   if not page:break
  root=R/'data/canonical-pilot02-results';root.mkdir(exist_ok=True);output_names=[n for n in objects if n!='inputs.tar'];size=sum(int(objects[n]['size']) for n in output_names);assert size<2*1024**3;assert shutil.disk_usage(root).free>3*size+10*1024**3
  from canonical_transfer_guard02 import check_transfer_bound
  save('results/canonical-pilot02-collection-transfer-bound.json',check_transfer_bound(read('results/canonical-pilot02-prepared.json')['input_bytes'],size))
  def fetch(n,sha=None):
   assert Path(n).name==n and n not in ('.','..');m=objects[n];p=root/n
   if not p.exists():
    part=root/(n+'.partial');assert not part.exists(),'Diagnose preserved partial download before retry: '+str(part)
    u=base+'/'+urllib.parse.quote(m['name'],safe='')+'?'+urllib.parse.urlencode({'alt':'media','generation':m['generation']})
    with get(u) as src,part.open('xb') as dst:shutil.copyfileobj(src,dst)
    check(part,m,sha);part.rename(p)
   check(p,m,sha)
  def check(p,m,sha):
   b=p.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'],p
   if sha:assert hashlib.sha256(b).hexdigest()==sha,p
  # Preserve all available evidence even if the task failed or reached its deadline.
  with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,output_names))
  save('results/canonical-pilot02-output-inventory.json',{'prefix':PREFIX,'bytes':size,'objects':{n:objects[n] for n in output_names}})
  if 'complete.json' not in objects:
   proof=dict(passed=False,experiment_complete=False,terminal=status['state'],cleanup_verified=True,preserved_outputs=output_names,automatic_retry=False)
   save('results/canonical-pilot02-incomplete.json',proof);save('results/canonical-pilot02-collected.json',proof);print('INCOMPLETE; evidence and checkpoints retained; diagnose before any continuation');return
  complete=json.loads((root/'complete.json').read_text());assert complete['passed'] and complete['arms_completed']==2 and complete['epochs_per_arm']==600 and complete['test_evaluated'] is False
  for n,h in complete['manifest'].items():fetch(n,h)
  replay=json.loads((root/'optimizer-replay.json').read_text());assert replay['passed'] and 'L4' in replay['device_name'];assert all(a['serialized_restore_map_location']=='cpu' and a['optimizer_device_layout_preserved'] for a in replay['arms']);freeze=json.loads((root/'selection-freeze.json').read_text());assert freeze['test_evaluated'] is False and len(freeze['arms'])==2
  barrier=objects['selection-freeze.json']['timeCreated'];assert freeze['confirmation_scored'] is False
  for name in ['comparison.json','confirmation-baseline.json','confirmation-no-change.json']+[arm+suffix for arm in ['canonical_half','canonical_full'] for suffix in ['-untrained-confirmation.json','-confirmation.json']]:assert objects[name]['timeCreated']>=barrier,name
  for arm in ['canonical_half','canonical_full']:
   assert objects[arm+'-selected.pt']['timeCreated']<=barrier
   for epoch in range(1,601):assert arm+f'-epoch{epoch:03}.pt' in complete['manifest']
  assert not any('test-predictions' in n or 'horizon' in n for n in output_names)
  comparison=json.loads((root/'comparison.json').read_text());assert comparison['test_evaluated'] is False and comparison['winner']==freeze['winner']
  assert complete['selection_frozen_before_confirmation'] is True and complete['repair_acceptance_passed']==comparison['passed']
  proof=dict(passed=True,experiment_complete=True,repair_acceptance_passed=comparison['passed'],checks=comparison['checks'],objects_verified=len(output_names),bytes=size,all_epoch_checkpoints_preserved=True,optimizer_replay_passed=True,selection_before_comparison=True,test_not_evaluated=True,cleanup_verified=True)
  save('results/canonical-pilot02-collected.json',proof);print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
