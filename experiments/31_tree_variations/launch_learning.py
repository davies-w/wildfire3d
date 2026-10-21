from pathlib import Path
import json,time,fcntl,yaml
from cloud import gc,read,save
R=Path(__file__).parent
with (R/'data/budget.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 for g in read('groups.json'):
  if g['phase']!='test':assert read(f"jobs/{g['id']}/completion.json")['all_full_horizon']
 assert not gc('compute','instances','list') and not gc('batch','jobs','list','--location=us-central1')
 ledger=read('budget.json');key='gpu-learning-01';assert key not in ledger['reservations'];assert ledger['reserved_usd']+1<=ledger['authorized_usd']+1e-8
 deployed=gc('workflows','describe','fds-gpu31-learning01','--location=us-central1');assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((R/'gpu-workflow.yaml').read_text())
 ledger['reserved_usd']=round(ledger['reserved_usd']+1,4);ledger['reservations'][key]=dict(state='reserved',allowance_usd=1,reserved_unix=time.time(),queue_limit_s=1200,vm_age_limit_s=2100,absolute_limit_s=3300,retries=0);save('budget.json',ledger)
 e=gc('workflows','execute','fds-gpu31-learning01','--location=us-central1');save('results/gpu-execution.json',e);ledger['reservations'][key].update(state='submitted',execution=e['name']);save('budget.json',ledger);print(e['name'],flush=True)
