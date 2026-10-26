"""Single campaign owner; no automatic compute retry or duplicate submission."""
from pathlib import Path
import fcntl,time,traceback,json
from cloud import read,save,launch,collect,B,active_groups
from coverage_review import main as review
R=Path(__file__).resolve().parent
with (R/'data/dispatcher.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  while True:
   groups=active_groups();active=[];b=json.loads(B.read_text())
   for g in groups:
    n=g['id'];f=R/'jobs'/n
    if (f/'completion.json').exists():continue
    if (f/'execution.json').exists():
     if not collect(n):active.append(n)
    else:assert b['reservations'][n]['state']=='reserved_before_upload','Unknown submission outcome; investigate, never retry blindly'
   coverage=groups[0]
   if (R/'jobs'/coverage['id']/'completion.json').exists() and not (R/'results/coverage-review.json').exists():review()
   ready=(R/'results/coverage-review.json').exists()
   for g in groups:
    if len(active)>=24:break
    if g['phase']!='coverage' and not ready:continue
    if (R/'jobs'/g['id']/'execution.json').exists():continue
    launch(g['id']);active.append(g['id'])
   if all((R/'jobs'/g['id']/'completion.json').exists() for g in groups):save('results/simulations-complete.json',dict(complete=True,new_runs=1560));break
   time.sleep(60)
 except BaseException:save('results/dispatcher-error.json',dict(error=traceback.format_exc()));raise
