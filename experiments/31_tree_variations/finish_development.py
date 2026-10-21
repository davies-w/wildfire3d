import fcntl,time,json
from pathlib import Path
import cloud
R=Path(__file__).parent
with (R/'data/collector.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 groups=[g for g in cloud.read('groups.json') if g['phase']!='test']
 while groups:
  for g in groups[:]:
   if (R/f"jobs/{g['id']}/completion.json").exists():groups.remove(g);continue
   try:r=cloud.collect(g['id'])
   except Exception as e:print('COLLECTION_PENDING',g['id'],type(e).__name__,str(e)[:300],flush=True);continue
   if r.get('collected')==len(g['cases']):
    assert r['all_full_horizon'],r
    print('COLLECTED',g['id'],flush=True);groups.remove(g)
  if groups:time.sleep(45)
 print('ALL_DEVELOPMENT_COLLECTED',flush=True)
