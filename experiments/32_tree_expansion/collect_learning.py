"""Retrieve small results/weights and verify cloud training cleanup; keep prediction bulk in GCS."""
from pathlib import Path
import json,time,fcntl,subprocess,tarfile,hashlib
from cloud import gc,read,save,G,PROJECT
R=Path(__file__).parent
with (R/'data/gpu-collector.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 e=read('results/gpu-execution.json')['name'].split('/')[-1];s=gc('workflows','executions','describe',e,'--workflow=fds-gpu32-learning01','--location=us-central1');save('results/gpu-status.json',s)
 if s['state']=='ACTIVE':print('ACTIVE');raise SystemExit(0)
 inv={k:gc(*a,'--filter=labels.trial_id=gpu32-learning01') for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};save('results/gpu-cleanup.json',inv);assert not any(inv.values())
 dest=R/'data/gpu/cloud';dest.mkdir(parents=True,exist_ok=True)
 for n in ['complete.json','prediction-freeze.json','learning.json','outputs.tar','resume-check.json']:
  if not (dest/n).exists():subprocess.run([G,'storage','cp','gs://'+PROJECT+'-trial/expansion32/gpu01/'+n,str(dest/n)],check=True)
 done=json.loads((dest/'complete.json').read_text());assert done['success'] and hashlib.sha256((dest/'outputs.tar').read_bytes()).hexdigest()==done['output_sha256']
 with tarfile.open(dest/'outputs.tar') as t:t.extractall(R,filter='data')
 freeze=read('results/prediction-freeze.json')
 for name,h in freeze['files'].items():
  if not name.endswith('.npz'):assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
 # Prediction objects remain cloud-resident; hashes are frozen and verified when used for final evaluation.
 with (R/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);ledger=read('budget.json');ledger['reservations']['gpu-learning-01'].update(state='terminal_cleanup_verified',completed_unix=time.time());save('budget.json',ledger)
 save('results/learning-collected.json',dict(complete=True,predictions_location='gs://'+PROJECT+'-trial/expansion32/gpu01/predictions/',fresh_test_truth_accessed=False));print('GPU_COLLECTED')
