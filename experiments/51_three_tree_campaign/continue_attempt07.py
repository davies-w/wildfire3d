"""Authorized continuation: wait for full06 audit, then strict07 readiness/preservation/launch once."""
from cloud07 import *
import sys,lzma,re
repo=R.parents[1]
def run(name,*args):subprocess.run([sys.executable,str(R/name),*args],check=True,cwd=repo)
with (P/'continuation.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (P/'submission-intent.json').exists(),'Never duplicate launch'
 for tick in range(180):
  a=R/'private06/terminal-archive.json'
  if a.exists() and json.loads(a.read_text())['passed']:break
  print('Waiting for full immutable Attempt6 audit',tick,flush=True);time.sleep(30)
 else:raise RuntimeError('Audit wait expired; no launch')
 assert json.loads((R/'private06/allocation-summary.json').read_text())['passed']
 if not (R/'private06/grants-retired.json').exists():run('retire_grants06.py')
 if not (R/'private06/closed.json').exists():run('close_campaign06.py')
 assert not (R/'data/cloud07').exists(),'Inspect partial preparation before repeating'
 run('prepare_campaign07.py');run('finalize_operations07.py')
 expected=[171,12,17]+list(range(176,1704));D=R/'data/cloud07'
 for i,oldindex in enumerate(expected):
  olditem=json.loads((R/'data/cloud06/inputs/items'/f'{oldindex}.json').read_text());newitem=json.loads((D/'inputs/items'/f'{i}.json').read_text());assert olditem['case']==newitem['case']
  old=json.loads(lzma.decompress((R/'data/cloud06/inputs'/(olditem['id']+'.xz')).read_bytes()));new=json.loads(lzma.decompress((D/'inputs'/(newitem['id']+'.xz')).read_bytes()))
  for name in old:
   if name not in ['transport.py','checkpoint_control.py']:assert old[name]==new[name],name
  assert not any(re.search(r'PRIVATE KEY|hf_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{25,}',v) for v in new.values())
 save('bundle-validation.json',dict(passed=True,cases=len(expected),original_decks_worker_unchanged=True))
 run('deploy_campaign07.py')
 for tick in range(120):
  e=json.loads((P/'readiness-execution.json').read_text());s=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1');save('readiness-status.json',s)
  if s['state']=='SUCCEEDED':
   children=[gc('workflows','executions','describe',n.split('/')[-1],'--workflow='+n.split('/')[-3],'--location=us-central1') for n in json.loads(s['result'])['children']]
   assert all(c['state'] in ['ACTIVE','SUCCEEDED','QUEUED'] for c in children)
   if all(c['state']=='SUCCEEDED' for c in children):break
  else:assert s['state'] in ['ACTIVE','QUEUED']
  time.sleep(5)
 else:raise RuntimeError('Readiness bounded timeout; no launch')
 run('validate_readiness07.py')
 f=R/'dvc.yaml';s=f.read_text();assert '\n  cloud07:' not in s;f.write_text(s+'  cloud07:\n    cmd: ../../.venv/bin/python prepare_campaign07.py\n    frozen: true\n    outs:\n    - data/cloud07\n')
 helper=repo/'scripts/dvc_hf.py';subprocess.run([sys.executable,str(helper),'commit','experiments/51_three_tree_campaign/dvc.yaml:cloud07'],cwd=repo,check=True)
 state=repo/'experiments/43_repository_preservation/results/direct-hf';plan=json.loads((state/'plan.json').read_text())
 for o in plan['objects'].values():assert o.get('directory') or o['source'].startswith('experiments/51_three_tree_campaign/data/cloud07/')
 dedicated=P/'scientific-plan.json';dedicated.write_bytes((state/'plan.json').read_bytes());print('Reviewed scientific input plan',len(plan['objects']),sha(dedicated),flush=True)
 subprocess.run([sys.executable,str(helper),'push','--plan',str(dedicated)],cwd=repo,check=True)
 v=json.loads((state/'upload-verification.json').read_text());assert v['passed'] and v['objects']==len(plan['objects']) and v['remote_size_and_xet_verified'] and v['directory_anonymous_readback'] and v['plan_sha256']==sha(dedicated);save('input-upload-verification.json',v)
 paths=[str(x.relative_to(repo)) for x in R.glob('*07.py')]+[str(x.relative_to(repo)) for x in R.glob('rolling07-*.yaml')]+[str((R/n).relative_to(repo)) for n in ['README.md','dvc.yaml','dvc.lock','audit_allocation06.py','audit_terminal06.py']]
 subprocess.run(['git','add','--',*paths],cwd=repo,check=True);subprocess.run(['git','commit','-m','Validate and preserve Experiment51 Attempt7 before authorized launch'],cwd=repo,check=True);subprocess.run(['git','push','origin','codex/ignition-surrogate-pilot'],cwd=repo,check=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/ignition-surrogate-pilot'],cwd=repo,text=True).split()[0];assert head==remote
 pkg=json.loads((P/'package.json').read_text());save('preservation.json',dict(passed=True,index_sha256=pkg['index_sha256'],input_verification=v,git_remote_verified=head))
 run('launch_campaign07.py')
 e=json.loads((P/'execution.json').read_text());(R/'launch-record07.json').write_text(json.dumps(dict(workflow=WF,execution=e['name'].split('/')[-1],created_at=e['startTime'],runs=1531,prior_accepted=468,first_case='tree51_000446_baseline',diagnosed_fresh_replacements=3,pending_review=1,index_sha256=pkg['index_sha256']),indent=2)+'\n')
 subprocess.run(['git','add',str((R/'launch-record07.json').relative_to(repo))],cwd=repo,check=True);subprocess.run(['git','commit','-m','Record Experiment51 Attempt7 one-time submission'],cwd=repo,check=True);subprocess.run(['git','push','origin','codex/ignition-surrogate-pilot'],cwd=repo,check=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/ignition-surrogate-pilot'],cwd=repo,text=True).split()[0]==head
 print('ATTEMPT7 SUBMITTED ONCE; starting continuous canary verification',e['name'],flush=True)
 run('await_canary07.py')
