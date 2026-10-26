"""Collect immutable cloud completion markers; never launch or alter cloud jobs."""
from pathlib import Path
import json,fcntl,subprocess
from cloud import R,G,BUCKET,gc,download_summary,read

def main():
 with (R/'data/cloud-collector.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  root=R/'data/cloud-collected';root.mkdir(exist_ok=True)
  prefix='gs://'+BUCKET+'/density36/'
  p=subprocess.run([G,'storage','ls',prefix+'orchestration/completed/*.json'],capture_output=True,text=True,timeout=120)
  if p.returncode:
   assert 'matched no objects' in p.stderr.lower() or 'no urls matched' in p.stderr.lower(),p.stderr
   return
  groups={g['id']:g for g in read('active-groups.json')};freeze=read('results/input-freeze.json')['cases']
  for uri in p.stdout.splitlines():
   n=uri.rsplit('/',1)[-1].removesuffix('.json');assert n in groups
   d=root/n;d.mkdir(exist_ok=True)
   if (d/'verified.json').exists():continue
   download_summary(uri,d/'cloud-completion.json');marker=json.loads((d/'cloud-completion.json').read_text())
   assert marker['group']==n and marker['cases']==len(groups[n]['cases']) and marker['all_full_horizon']
   download_summary(prefix+n+'/job-status.json',d/'job-status.json');assert json.loads((d/'job-status.json').read_text())['status']['state']=='SUCCEEDED'
   for c in groups[n]['cases']:
    download_summary(prefix+n+'/'+c+'.summary.json',d/(c+'.json'));s=json.loads((d/(c+'.json')).read_text())
    assert s['result']['full_horizon'] and s['resume']['passed'] and s['checkpoint_manifest']['files']
    assert s['deck_sha256']==freeze[c] and s['result']['binary_sha256']=='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
    m=gc('storage','objects','describe',prefix+n+'/'+c+'.tar.gz');assert int(m['size'])==s['raw_bytes']
    (d/(c+'-raw-object.json')).write_text(json.dumps(m,indent=2)+'\n')
   inventory={key:gc(*args,'--filter=labels.trial_id='+n) for key,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
   assert not any(inventory.values());(d/'cleanup.json').write_text(json.dumps(inventory,indent=2)+'\n')
   (d/'verified.json').write_text(json.dumps({'group':n,'cases':len(groups[n]['cases']),'summaries_and_raw_sizes_verified':True,'raw_sha_verification_pending':True,'cleanup_verified':True},indent=2)+'\n')
   print('COLLECTED',n,flush=True)
  rows=[json.loads(p.read_text()) for p in root.glob('*/verified.json')]
  (R/'results/cloud-collection.json').write_text(json.dumps({'groups':len(rows),'cases':sum(x['cases'] for x in rows),'raw_sha_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
