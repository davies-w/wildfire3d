import time,fcntl,json
from pathlib import Path
import cloud
R=Path(__file__).parent
with (R/'data/test-collector.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 g=next(g for g in cloud.read('groups.json') if g['phase']=='test')
 while True:
  try:r=cloud.collect(g['id'])
  except Exception as e:print('COLLECTION_PENDING',str(e)[:300],flush=True);time.sleep(30);continue
  if r.get('collected')==2:assert r['all_full_horizon'];print('FRESH_TESTS_COLLECTED',flush=True);break
  time.sleep(45)
