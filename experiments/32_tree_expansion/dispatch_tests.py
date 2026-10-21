"""One locked fresh-test dispatcher; requires frozen forecasts and completed learning."""
import fcntl,time,traceback
from pathlib import Path
from cloud import read,save,launch,collect
R=Path(__file__).parent
if __name__=='__main__':
 with (R/'data/test-dispatcher.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   assert read('results/learning-collected.json')['complete']
   groups=[g for g in read('groups.json') if g['phase']=='test']
   for g in groups:
    if g['id'] not in read('budget.json')['reservations']:launch(g['id'],25)
   while True:
    complete=True
    for g in groups:
     n=g['id']
     if (R/'jobs'/n/'completion.json').exists():assert read(f'jobs/{n}/completion.json')['all_full_horizon'];continue
     result=collect(n)
     if result['state']=='ACTIVE':complete=False
     else:assert result.get('all_full_horizon'),result
    if complete:save('results/test-simulations-complete.json',dict(complete=True,time_unix=time.time()));break
    time.sleep(60)
  except BaseException:save('results/test-dispatcher-error.json',dict(error=traceback.format_exc(),time_unix=time.time()));raise
