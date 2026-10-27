"""Remove only the completed timing job's exact temporary read grant."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,PROJECT,gc,read,save
assert read('results/model-pair-timing-collected.json')['passed']
assert read('results/model-pair-timing-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
c=read('results/model-pair-timing-read-condition.json');assert c['title']=='density36-model-pair-preflight01-read'
subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/model-pair-timing-read-condition.json')],check=True,capture_output=True)
a=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)
assert not any(b.get('condition')==c for b in a['bindings'])
save('results/model-pair-timing-permission-removed.json',{'exact_grant_removed':True,'condition':c,'raw_and_outputs_preserved':True})
