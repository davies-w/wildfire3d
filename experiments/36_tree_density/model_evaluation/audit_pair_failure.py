"""Preserve diagnosed pre-training failure and verify cleanup before repair."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,PROJECT,BUCKET,gc,read,save,download_summary
root=R/'data/model-pair-failure';root.mkdir(exist_ok=True);prefix='gs://'+BUCKET+'/density36/model-pair-training01/'
for name in ('job-status.json','transport-cloud-check.json'):download_summary(prefix+name,root/name)
(root/'bootstrap-error.txt').write_bytes(subprocess.run([G,'storage','cat',prefix+'bootstrap-error.txt'],capture_output=True,check=True).stdout)
assert 'Expected all tensors to be on the same device' in (root/'bootstrap-error.txt').read_text()
assert json.loads((root/'job-status.json').read_text())['status']['state']=='FAILED'
e=read('results/model-pair-training-execution.json')['name'].split('/');status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');assert status['state'] in ('SUCCEEDED','FAILED');save('results/model-pair-training-status.json',status)
inv={k:gc(*v) for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inv.values());save('results/model-pair-training-cleanup.json',inv)
names=subprocess.run([G,'storage','ls',prefix],capture_output=True,text=True,check=True).stdout;assert 'epoch' not in names and 'selected' not in names
c=read('results/model-pair-training-read-condition.json')
subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/model-pair-training-read-condition.json')],check=True,capture_output=True)
assert not any(b.get('condition')==c for b in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings'])
save('results/model-pair-training-failure.json',dict(diagnosed=True,no_real_training_started=True,cleanup_empty=True,exact_read_grant_removed=True,error='Synthetic resume audit compared CPU AdamW step counter with GPU deserialized counter',repair='Compare detached optimizer-state values on CPU; model/loss/data unchanged',original_execution=status['name']))
