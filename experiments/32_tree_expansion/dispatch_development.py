"""Single locked development dispatcher. No retries, no test launches, bounded cloud jobs."""
import fcntl,time,traceback
from pathlib import Path
from cloud import read,save,launch,collect
from coverage_review import main as review
R=Path(__file__).parent
def main():
 with (R/'data/dispatcher.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   groups=[g for g in read('groups.json') if g['phase']!='test'];ledger=read('budget.json');active=[]
   for g in groups:
    n=g['id'];folder=R/'jobs'/n
    if (folder/'completion.json').exists():
     assert read(f'jobs/{n}/completion.json')['all_full_horizon'];continue
    if n not in ledger['reservations']:continue
    assert (folder/'execution.json').exists(),'Reserved but submission outcome unknown: investigate; never resubmit'
    result=collect(n)
    if result['state']=='ACTIVE':active.append(n)
    else:assert result.get('all_full_horizon'),result
   coverage=next(g for g in groups if g['phase']=='coverage')
   if (R/'jobs'/coverage['id']/'completion.json').exists() and not (R/'results/coverage-review.json').exists():review()
   if (R/'results/coverage-review.json').exists():
    assert read('results/coverage-review.json')['passed']
    for g in groups:
     if len(active)>=6:break
     if g['id'] not in read('budget.json')['reservations']:launch(g['id'],25);active.append(g['id'])
   if all((R/'jobs'/g['id']/'completion.json').exists() for g in groups):
    save('results/development-complete.json',dict(complete=True,groups=len(groups),finished_unix=time.time()));print('DEVELOPMENT_COMPLETE',flush=True);return
   time.sleep(60)
if __name__=='__main__':
 try:main()
 except BaseException:
  save('results/dispatcher-error.json',dict(time_unix=time.time(),error=traceback.format_exc()));raise
