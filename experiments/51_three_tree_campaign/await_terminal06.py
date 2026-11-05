"""Bounded read-only drain watch, then immutable terminal preservation/audit only."""
from cloud06 import *
import sys
assert not (P/'terminal-archive.json').exists(),'Inspect existing terminal audit; never duplicate'
with (P/'terminal-watch.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for tick in range(180):
  subprocess.run([sys.executable,str(R/'monitor_campaign06.py')],check=True,stdout=subprocess.DEVNULL)
  s=json.loads((P/'status.json').read_text());assert s['controller']['state']!='ACTIVE'
  cases=gc('workflows','executions','list',WF+'-case','--location=us-central1');epochs=gc('workflows','executions','list',WF+'-epoch','--location=us-central1');save('case-executions.json',cases);save('epoch-executions.json',epochs)
  active=sum(x['state']=='ACTIVE' for x in cases+epochs);print('Drain',tick,'children',active,'jobs',len(s['jobs']),'VMs',len(s['vms']),flush=True)
  if active==0 and not s['jobs'] and not s['vms']:
   assert not gc('compute','disks','list','--filter=name~t51r06')
   subprocess.run([sys.executable,str(R/'inspect_outputs06.py')],check=True,stdout=subprocess.DEVNULL)
   assert not (P/'terminal-objects.json').exists();(P/'terminal-objects.json').write_bytes((P/'objects.json').read_bytes())

   print('TERMINAL SNAPSHOT READY; audits pending; grants and ledger unchanged',flush=True);break
  time.sleep(30)
 else:raise RuntimeError('Drain watch bounded timeout; no cleanup or ledger mutation performed')
