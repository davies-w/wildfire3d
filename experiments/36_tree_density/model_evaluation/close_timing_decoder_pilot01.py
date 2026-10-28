"""Remove only the terminal joint decoder pilot's exact temporary read grant."""
import subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,PROJECT,gc,read,save
terminal=read('results/timing-decoder-pilot01-status.json');assert terminal['state']!='ACTIVE'
proof=read('results/timing-decoder-pilot01-collected.json') if (R/'results/timing-decoder-pilot01-collected.json').exists() else read('results/timing-decoder-pilot01-incomplete.json');assert proof['cleanup_verified']
assert read('results/timing-decoder-pilot01-cleanup.json')=={'jobs':[],'instances':[],'disks':[]}
for cmd in [('batch','jobs','list','--location=us-central1'),('compute','instances','list'),('compute','disks','list')]:assert not gc(*cmd,'--filter=labels.trial_id=gpu36-timing01')
c=read('results/timing-decoder-pilot01-read-condition.json');assert c['title']=='density36-timing-decoder-pilot01-read'
policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)
if any(b.get('condition')==c and 'serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com' in b.get('members',[]) for b in policy['bindings']):
 subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(R/'results/timing-decoder-pilot01-read-condition.json')],check=True,capture_output=True)
policy=gc('storage','buckets','get-iam-policy','gs://'+BUCKET);assert not any(b.get('condition')==c for b in policy['bindings'])
save('results/timing-decoder-pilot01-permission-removed.json',{'exact_grant_removed':True,'condition':c,'all_inputs_outputs_and_checkpoints_preserved':True})
