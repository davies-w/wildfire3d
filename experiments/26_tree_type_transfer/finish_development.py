"""Single development collector; never submits jobs or opens held-out outputs."""
import fcntl,json,time,traceback,subprocess
from cloud import ROOT,read,save,collect
from extract import extract
lock=(ROOT/'data/development-collector.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
end=time.time()+4*3600
while time.time()<end:
 try:
  groups=[g for g in read('groups.json') if g['phase']=='development'];done=[];failed=[]
  for g in groups:
   if not (ROOT/'jobs'/g['id']/'execution.json').exists():continue
   completion=ROOT/'jobs'/g['id']/'completion.json'
   r=json.loads(completion.read_text()) if completion.exists() else collect(g['id'])
   if r['state']=='ACTIVE':continue
   if r.get('collection_error') or not r.get('all_full_horizon'):
    save('results/'+g['id']+'-collection-error.json',r);failed.append(r)
    # Preserve and extract any completed cases preceding a worker failure.
    for name in g['cases']:
     raw=ROOT/'data/cloud'/name/'result.json'
     if raw.exists() and json.loads(raw.read_text()).get('full_horizon') and not (ROOT/'data/extracted'/(name+'.json')).exists():
      extract(next(c for c in read('cases.json') if c['case']==name))
    continue
   for name in g['cases']:
    if not (ROOT/'data/extracted'/(name+'.json')).exists():
     c=next(c for c in read('cases.json') if c['case']==name);assert c['split'] in ['train','validation'];extract(c)
   done.append(g['id'])
  save('results/development-progress.json',dict(completed_groups=done,expected_groups=[g['id'] for g in groups],failed_groups=failed))
  if len(done)+len(failed)==len(groups) and failed:
   save('results/development-partial-summary.json',dict(completed_groups=done,failed_groups=failed,full_horizon=False,test_outputs_read=False));break
  if len(done)==len(groups):
   save('results/development-summary.json',dict(completed_groups=done,full_horizon=True,test_outputs_read=False));print('DEVELOPMENT COLLECTED',flush=True);break
  time.sleep(45)
 except SystemExit:raise
 except Exception:
  (ROOT/'results/development-collector-error.txt').write_text(traceback.format_exc());raise
else:raise SystemExit('Collector deadline reached; verify pending controllers, no continuation')
