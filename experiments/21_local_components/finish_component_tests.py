"""One local collector for already submitted frozen tests; never launches/retries jobs."""
import fcntl,json,subprocess,sys,time
from scene import ROOT
lock=(ROOT/'data/component-test-collector.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
names=json.loads((ROOT/'results/component-test-prediction-freeze.json').read_text())['cases']
end=json.loads((ROOT/'budget-overnight.json').read_text())['end_unix']
while time.time()<end+300:
 pending=[n for n in names if not (ROOT/'results'/f'{n}-test.json').exists() and not (ROOT/'results'/f'{n}-failure.json').exists()]
 if not pending:break
 subprocess.run([sys.executable,str(ROOT/'component_test_control.py'),'collect',*pending],check=True)
 ready=[n for n in pending if (ROOT/'results'/f'{n}-collected.json').exists()]
 if ready:
  subprocess.run([sys.executable,str(ROOT/'analyze_component_tests.py'),*ready],check=True)
  subprocess.run([str(ROOT.parents[1]/'.venv/bin/dvc'),'commit','-f',*[n+'_'+s for n in ready for s in ['collect','analyze']]],cwd=ROOT,check=True)
  print('ANALYZED',ready,flush=True)
 if all((ROOT/'results'/f'{n}-test.json').exists() or (ROOT/'results'/f'{n}-failure.json').exists() for n in names):break
 time.sleep(45)
print('COLLECTOR_FINISHED',flush=True)
