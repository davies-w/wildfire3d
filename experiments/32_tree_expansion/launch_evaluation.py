"""Single $0.50 reserved evaluation attempt; no training or retries."""
from pathlib import Path
import json,time,fcntl,subprocess,yaml
from cloud import gc,read,save,G,PROJECT
R=Path(__file__).parent
with (R/'data/budget.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert read('results/test-simulations-complete.json')['complete'];ledger=read('budget.json');key='gpu-evaluation-01';assert key not in ledger['reservations'] and ledger['reserved_usd']+.5<=25
 assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
 uri='gs://'+PROJECT+'-trial/expansion32/evaluation01/overlay.tar'
 if not (R/'results/evaluation-overlay-upload.json').exists():
  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/evaluation-overlay.tar'),uri],check=True);save('results/evaluation-overlay-upload.json',gc('storage','objects','describe',uri))
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];f=R/'evaluation-workflow.yaml';gc('workflows','deploy','fds-gpu32-evaluation01','--location=us-central1','--source='+str(f),'--service-account='+sa);assert yaml.safe_load(gc('workflows','describe','fds-gpu32-evaluation01','--location=us-central1')['sourceContents'])==yaml.safe_load(f.read_text())
 ledger['reserved_usd']=round(ledger['reserved_usd']+.5,4);ledger['reservations'][key]=dict(state='reserved',allowance_usd=.5,reserved_unix=time.time(),vm_age_limit_s=1800,absolute_limit_s=3000,retries=0);save('budget.json',ledger)
 e=gc('workflows','execute','fds-gpu32-evaluation01','--location=us-central1');save('results/evaluation-execution.json',e);ledger['reservations'][key].update(state='submitted',execution=e['name']);save('budget.json',ledger);print('EVALUATION_SUBMITTED')
