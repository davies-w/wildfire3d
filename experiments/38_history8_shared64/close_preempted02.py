"""Remove only preempted attempt01 input read grant after verified archival/cleanup."""
from pathlib import Path
import json,sys,subprocess
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET,PROJECT
assert json.loads((R/'results02/preemption-audit.json').read_text())['passed']
inv={k:gc(*a,'--filter=labels.trial_id=gpu38-history02') for k,a in dict(jobs=('batch','jobs','list','--location=us-west1'),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(inv.values())
p=R/'results02/read-condition.json';c=json.loads(p.read_text());assert c['title']=='history38-training02-read'
if any(b.get('condition')==c for b in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings']):subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(p)],check=True,capture_output=True)
assert not any(b.get('condition')==c for b in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings'])
(R/'results02/preempted-closed.json').write_text(json.dumps(dict(passed=True,cleanup=inv,exact_grant_removed=c,artifacts_preserved=True),indent=2)+'\n')
