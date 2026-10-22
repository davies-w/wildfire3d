"""One locked collector; never launches or retries a paid job."""
import fcntl,json,time,traceback
from pathlib import Path
from cloud import ROOT,collect,read,save
from extract import extract
lock=(ROOT/'data/calibration-collector.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
name='t26-calibration-0'
if (ROOT/'results/calibration-summary.json').exists():raise SystemExit('Already collected')
ledger=read('budget.json');deadline=ledger['reservations'][name]['reserved_unix']+6600
while time.time()<deadline:
 try:
  result=collect(name)
  if result['state']=='ACTIVE':time.sleep(40);continue
  if result.get('collection_error'):
   save('results/calibration-collector-error.json',result);raise SystemExit('Terminal job missing evidence; diagnosis required, no retry')
  cases=[c for c in read('cases.json') if c['case'] in next(g for g in read('groups.json') if g['id']==name)['cases']]
  reports=[extract(c) for c in cases]
  save('results/calibration-summary.json',dict(completion=result,cases=reports,decision='Needs scientific review before remaining development submission; no automatic release.'))
  print('CALIBRATION COLLECTED',flush=True);break
 except SystemExit:raise
 except Exception:
  (ROOT/'results/calibration-collector-error.txt').write_text(traceback.format_exc());raise
else:raise SystemExit('Collector deadline reached; verify cloud cleanup, no continuation authorized')
