"""One locked collector for authorized submissions; never launches paid work."""
import fcntl,json,time,subprocess,sys,traceback
from pathlib import Path
from cloud import collect,ROOT
lock=(ROOT/'data/collector.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
ledger=json.loads((ROOT/'budget.json').read_text());end=max(v['reserved_unix']+v['duration_s'] for v in ledger['reservations'].values())+1200
while time.time()<end:
 try:
  rows=collect()
  if len(rows)==6 and all(r['state']!='ACTIVE' for r in rows):
   if any('collection_error' in r for r in rows):
    (ROOT/'results/collector-needs-attention.json').write_text(json.dumps(rows,indent=2))
   subprocess.run([sys.executable,str(ROOT/'analyze.py')],check=True)
   subprocess.run([sys.executable,str(ROOT/'field_metrics.py')],check=True)
   subprocess.run([str(ROOT.parents[1]/'.venv/bin/dvc'),'commit','-f','collect','analyze','fields'],cwd=ROOT,check=True)
   (ROOT/'results/collector-complete.json').write_text(json.dumps(dict(finished_unix=time.time(),collected_cases=len(list((ROOT/'data/cloud').glob('*/result.json'))))))
   print('COLLECTOR_FINISHED',flush=True);break
 except Exception:
  with (ROOT/'results/collector-errors.log').open('a') as f:f.write(traceback.format_exc())
  print('Collection/analysis error recorded; no paid retry',flush=True)
 time.sleep(45)
else:print('Collector deadline reached; inspect status and cleanup',flush=True)
