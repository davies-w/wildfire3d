"""Read-only Flex queue progress; never reads held-out scores or submits work."""
from pathlib import Path
import sys,json,subprocess,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
x=read('results/flex-queue-execution.json')['name'].split('/');state=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1')
jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id:gpu36-flex01');vms=gc('compute','instances','list','--filter=labels.trial_id:gpu36-flex01')
r=subprocess.run([G,'storage','ls','--recursive','gs://'+BUCKET+'/density36/flex-queue01/'],capture_output=True,text=True);assert r.returncode==0,r.stderr
names=r.stdout.splitlines();progress=[]
for n in range(1,10):
 prefix=f'/rotation{n}/';mine=[s for s in names if prefix in s];arms=[]
 for k in (0,1):
  checkpoints=[s.rsplit('/',1)[-1] for s in mine if f'fold{k:02}-epoch' in s and s.endswith('.pt')]
  arms.append(dict(model='plain' if k==0 else 'gated',checkpoint=max(checkpoints) if checkpoints else None,selected=any(s.endswith(f'fold{k:02}-selected.pt') for s in mine)))
 progress.append(dict(rotation=n,arms=arms,complete=any(s.endswith('/complete.json') for s in mine),errors=[s for s in mine if 'error' in s or s.endswith('/partial.json')]))
report=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow_state=state['state'],workflow_error=state.get('error'),jobs=[dict(name=j['name'],status=j['status']) for j in jobs],instances=[dict(name=v['name'],zone=v['zone'],status=v['status']) for v in vms],rotations=progress)
save('results/flex-queue-progress.json',report);print(json.dumps(report))
