"""Remove only this experiment's exact read bindings; reconcile measured terminal reservations."""
from pathlib import Path
import json,sys,subprocess,fcntl
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET,PROJECT,B
assert json.loads((R/'results/training02-collected.json').read_text())['passed']
inv={k:gc(*a,'--filter=labels.trial_id~gpu38-history02') for k,a in dict(jobs=('batch','jobs','list','--location=us-west1'),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(inv.values()),inv
removed=[]
for folder,name in [('results02','read-condition.json')]:
 p=R/folder/name;c=json.loads(p.read_text());assert c['title'].startswith('history38-')
 bindings=gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings']
 if any(b.get('condition')==c for b in bindings):subprocess.run([G,'storage','buckets','remove-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:fds-worker@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(p)],check=True,capture_output=True)
 assert not any(b.get('condition')==c for b in gc('storage','buckets','get-iam-policy','gs://'+BUCKET)['bindings']);removed.append(c)
with (B.parent/'data/budget.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text())
 for key,proof in [('history38-training02',R/'data/training02-results/job-status.json')]:
  assert json.loads(proof.read_text())['status']['state'] in ['FAILED','SUCCEEDED'];v=b['reservations'][key];assert v['cost']['stage'] in ['runtime_estimate','posted_billing_subject_to_adjustment'];assert v['cost']['usd']>0;v['state']='completed_reconciled';v['terminal_evidence']=str(proof.relative_to(R.parent.parent))
 b['reserved_usd']=sum(v['allowance_usd'] for v in b['reservations'].values() if v['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue']);B.write_text(json.dumps(b,indent=2)+'\n')
result=dict(passed=True,cleanup=inv,removed_exact_conditions=removed,raw_and_checkpoints_preserved=True,estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],headroom_usd=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd'],costs={k:b['reservations'][k]['cost'] for k in ['history38-training02']})
(R/'results02/closed.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
