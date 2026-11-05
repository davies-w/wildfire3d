"""Wait for the existing drain watcher, then perform read-only terminal audits."""
from cloud06 import *
import sys
with (P/'terminal-audit.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with (P/'terminal-watch.lock').open('r') as watcher:
  fcntl.flock(watcher,fcntl.LOCK_EX)
  assert (P/'terminal-objects.json').exists(),'Drain did not finish; no audit started'
  assert not (P/'terminal-archive.json').exists(),'Inspect existing audit before repeating'
  subprocess.run([sys.executable,str(R/'audit_terminal06.py')],check=True)
  subprocess.run([sys.executable,str(R/'audit_allocation06.py')],check=True)
  print('TERMINAL AUDITS PASS; no grants/budget/jobs changed',flush=True)
