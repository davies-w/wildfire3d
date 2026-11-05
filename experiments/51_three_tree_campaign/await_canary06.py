"""Bounded read-only watch, followed by independently proven one-time gate release.

No simulation submission/retry; only release_canary06's guarded admission marker.
"""
from cloud06 import *
import sys
with (P/'canary-watch.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for attempt in range(60):
  if (P/'canary-approved.json').exists():print('Gate already released; exiting',flush=True);break
  subprocess.run([sys.executable,str(R/'monitor_campaign06.py')],check=True,stdout=subprocess.DEVNULL)
  status=json.loads((P/'status.json').read_text());assert status['controller']['state']=='ACTIVE',status['controller']
  print('Canary',attempt,[(j['name'].split('/')[-1],j.get('status',{}).get('state')) for j in status['jobs']],flush=True)
  for j in status['jobs']:
   assert not (j['name'].endswith('/t51r06-c0') and j.get('status',{}).get('state')=='FAILED'),'Canary Batch failed; do not release gate'
  children=gc('workflows','executions','list',WF+'-case','--location=us-central1');done=False
  for e in children:
   s=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-case','--location=us-central1');a=json.loads(s.get('argument','{}'))
   if a.get('dry_run') or a.get('index')!=0:continue
   assert s['state'] not in ['FAILED','CANCELLED'],'Canary child failed; preserve and audit'
   if s['state']=='SUCCEEDED':
    v=json.loads(s['result']);assert v['passed'] and v['cleanup_verified'];done=True
  if done:
   subprocess.run([sys.executable,str(R/'inspect_outputs06.py')],check=True,stdout=subprocess.DEVNULL)
   subprocess.run([sys.executable,str(R/'collect_completed06.py'),'--wave','wave-000000'],check=True)
   subprocess.run([sys.executable,str(R/'release_canary06.py')],check=True)
   print('CANARY PASSED; independently verified gate released',flush=True);break
  time.sleep(30)
 else:raise RuntimeError('Bounded canary watch expired; no gate released')
