"""Verify empty compute inventory and remove only the exact temporary campaign grant."""
import datetime,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc

def main():
 assert json.loads((R/'results/dataset-completeness.json').read_text())['passed']
 inventory={k:gc(*args) for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
 assert not any(inventory.values()),'Compute resources remain; inspect before permission removal'
 condition=json.loads((R/'orchestration/read-condition.json').read_text())
 assert condition['title']=='density36-cloud-queue-read'
 policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)
 bindings=[b for b in policy['bindings'] if b.get('condition')==condition and b['role']=='roles/storage.objectViewer']
 expected={'serviceAccount:fds-worker@tmrw-wildfire-20261015.iam.gserviceaccount.com','serviceAccount:fds-watchdog@tmrw-wildfire-20261015.iam.gserviceaccount.com'}
 members={m for b in bindings for m in b['members']};assert members<=expected
 for member in sorted(members):
  subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member='+member,'--role=roles/storage.objectViewer','--condition-from-file='+str(R/'orchestration/read-condition.json')],check=True,capture_output=True)
 after=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)
 assert not any(b.get('condition')==condition and b['role']=='roles/storage.objectViewer' for b in after['bindings'])
 report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inventory':inventory,'exact_condition':condition,'removed_members':sorted(members),'exact_campaign_grant_absent':True,'raw_and_checkpoints_preserved':True}
 (R/'results/cloud-campaign-closed.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
