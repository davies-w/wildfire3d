"""Single-job admission and independent deadline; no retries or on-demand fallback."""
import argparse,base64,json,subprocess,fcntl,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent;P='tmrw-wildfire-20261015';G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+P,'--format=json'],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def generate(image):
 if not image.startswith(f'us-central1-docker.pkg.dev/{P}/fds/profile16@sha256:') or len(image.split('@sha256:')[-1])!=64:raise ValueError('Pinned profiling image required')
 template=yaml.safe_load((ROOT.parent/'15_resolution_cloud/workflow-science-recovery.yaml').read_text())
 steps=template['main']['steps'];assign=steps[0]['initialize']['assign'];job=assign[1]['job']
 assign[0]['deadline']='${sys.now() + 7140}'
 spec=job['taskGroups'][0]['taskSpec'];spec['maxRunDuration']='6900s'
 paths=[ROOT/'worker.py',ROOT/'manifest.json',*sorted((ROOT/'decks').glob('*.fds'))]
 payload={str(p.relative_to(ROOT)):base64.b64encode(p.read_bytes()).decode() for p in paths}
 bootstrap="import pathlib,base64,runpy; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; runpy.run_path('/study/worker.py',run_name='__main__')"
 spec['runnables']=[{'container':{'imageUri':image,'entrypoint':'python3','commands':['-c',bootstrap],'options':'--cpus=4 --memory=12g --pids-limit=256'}}]
 job['allocationPolicy']['labels']['trial_id']='study16';job['labels']['trial_id']='study16'
 for step in steps:
  if 'record' in step:step['record']['try']['args']['query']['name']='profile16/job-status.json'
  for k in ['list_workers','verify']:
   if k in step:step[k]['args']['query']['filter']='labels.trial_id = study16'
  if 'done' in step:step['done']['return']['mode']='profile16'
 for step in steps[2]['monitor']['try']['steps']:
  if 'wait' in step:step['wait']['args']['seconds']=30
 (ROOT/'job.json').write_text(json.dumps(job,indent=2)+'\n');(ROOT/'workflow.yaml').write_text(yaml.safe_dump(template,sort_keys=False))
 return template

def launch():
 with (ROOT/'data/launch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  marker=ROOT/'results/job-reservation.json'
  if marker.exists():raise RuntimeError('Single-job allowance already reserved; no automatic retry')
  j=json.loads((ROOT/'job.json').read_text());g=j['taskGroups'][0];s=g['taskSpec'];pol=j['allocationPolicy']['instances'][0]['policy']
  assert int(g['taskCount'])==int(g['parallelism'])==1 and s['maxRetryCount']==0 and s['maxRunDuration']=='6900s'
  assert pol['machineType']=='c3-standard-4' and pol['provisioningModel']=='SPOT' and int(pol['bootDisk']['sizeGb'])<=30
  deployed=gc('workflows','describe','fds-profile16','--location=us-central1')
  assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((ROOT/'workflow.yaml').read_text())
  for workflow in ['fds-science','fds-science-recovery','fds-timeout','fds-watchdog','fds-profile16']:
   if gc('workflows','executions','list',workflow,'--location=us-central1','--filter=state=ACTIVE'):raise RuntimeError('Active controller exists')
  if gc('batch','jobs','list','--location=us-central1') or gc('compute','instances','list'):raise RuntimeError('Existing cloud job/VM')
  record={'reserved_total_usd':.45,'created_unix':time.time(),'state':'reserved'};marker.write_text(json.dumps(record,indent=2)+'\n')
  result=gc('workflows','execute','fds-profile16','--location=us-central1');record.update(state='submitted',execution=result['name']);marker.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','launch']);ap.add_argument('--image');a=ap.parse_args()
 if a.action=='generate':generate(a.image)
 else:launch()
