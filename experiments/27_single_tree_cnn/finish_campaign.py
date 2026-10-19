"""Single locked authorized campaign: collect existing jobs, train, freeze, test, animate.
Requires reviewed pilot/domain decision. Reserves every launch; never retries.
"""
import fcntl,time,subprocess,sys,traceback
from cloud import ROOT,read,save,launch,collect
from fields import extract
lock=(ROOT/'data/campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
deadline=time.time()+8*3600

def process(phase):
 groups=[g for g in read('groups.json') if g['phase']==phase or (phase=='development' and g['phase'] in ['train','validation'])];pending={g['id'] for g in groups}
 while pending:
  assert time.time()<deadline,'Local driver deadline; no new submission'
  active=0
  ledger=read('budget.json')
  for name in sorted(pending):
   if name not in ledger['reservations']:continue
   g=next(g for g in groups if g['id']==name)
   if (ROOT/f'jobs/{name}/completion.json').exists():r=read(f'jobs/{name}/completion.json')
   else:r=collect(name)
   if r['state']=='ACTIVE':active+=1;continue
   assert not r.get('collection_error') and r.get('all_full_horizon'),r
   for c in read('cases.json'):
    if c['case'] in g['cases'] and not (ROOT/'data/fields'/(c['case']+'.json')).exists():extract(c)
   pending.remove(name)
  for name in sorted(pending):
   if name in read('budget.json')['reservations']:continue
   if active>=5:break
   launch(name,5);active+=1
  save('results/campaign-status.json',dict(phase=phase,pending=sorted(pending),reserved_usd=read('budget.json')['reserved_usd'],updated=time.time()))
  if pending:time.sleep(40)

def run(script):
 with (ROOT/'results'/(script+'.log')).open('w') as f:p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=max(1,deadline-time.time()))
 assert p.returncode==0,script+' failed'
try:
 assert read('results/pilot-decision.json')['release_development']
 process('development')
 if not (ROOT/'results/prediction-freeze.json').exists():run('cnn.py')
 else:
  import hashlib
  frozen=read('results/prediction-freeze.json')
  assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen['files'].items()),'Frozen artifacts changed; refuse resume'
 process('test');run('evaluate.py');run('learning_curve.py');run('animate.py')
 for script in ['verify_standalone.py','benchmark_inference.py','plot_test_histories.py','runtime_report.py','summarize_results.py','cost_report.py']:run(script)
 save('results/campaign-status.json',dict(phase='complete',reserved_usd=read('budget.json')['reserved_usd'],updated=time.time()))
except Exception:
 (ROOT/'results/campaign-error.txt').write_text(traceback.format_exc());raise
