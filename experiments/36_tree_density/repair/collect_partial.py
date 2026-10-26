"""Read-only collection of the nine-case recovery; retains original ownership elsewhere."""
import argparse,fcntl,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from cloud import R,BUCKET,gc,read,download_summary

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--proof',default='results/partial-recovery-workflow.json');args=ap.parse_args()
 with (R/'data/partial-collector.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  proof=read(args.proof);name=proof['group']
  execution=read('jobs/'+name+'/execution.json')['name'].split('/')
  status=gc('workflows','executions','describe',execution[-1],'--workflow='+execution[-3],'--location=us-central1')
  if status['state']=='ACTIVE':print('RECOVERY_ACTIVE');return
  root=R/'data/recovery-collected'/name;root.mkdir(parents=True,exist_ok=True)
  (root/'execution-status.json').write_text(json.dumps(status,indent=2)+'\n')
  inv={k:gc(*args,'--filter=labels.trial_id='+name) for k,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
  assert not any(inv.values()),inv
  (root/'cleanup.json').write_text(json.dumps(inv,indent=2)+'\n')
  prefix='gs://'+BUCKET+'/density36/'+name+'/'
  download_summary(prefix+'job-status.json',root/'job-status.json')
  assert json.loads((root/'job-status.json').read_text())['status']['state']=='SUCCEEDED','Diagnose interrupted recovery; do not retry automatically'
  freeze=read('results/input-freeze.json')['cases']
  for case in proof['cases']:
   download_summary(prefix+case+'.summary.json',root/(case+'.json'));s=json.loads((root/(case+'.json')).read_text())
   assert s['result']['full_horizon'] and s['resume']['passed'] and s['checkpoint_manifest']['files']
   assert s['deck_sha256']==freeze[case] and s['result']['binary_sha256']=='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
   meta=gc('storage','objects','describe',prefix+case+'.tar.gz');assert int(meta['size'])==s['raw_bytes']
   (root/(case+'-raw-object.json')).write_text(json.dumps(meta,indent=2)+'\n')
  report={'proof_file':args.proof,'group':name,'cases':proof['cases'],'cleanup_verified':True,'all_full_horizon':True,'raw_sha_verification_pending':True,'shared_permission_removal_deferred_until_entire_campaign_complete':True}
  (root/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
  (R/('results/partial-recovery-collection.json' if name=='x36-density-032-r1' else 'results/'+name+'-collection.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
