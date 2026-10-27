"""Read status and artifact names only; never read validation comparisons mid-run."""
import sys,subprocess,json,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
x=read('results/exposure-pilot02-execution.json')['name'].split('/');status=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');jobs=gc('batch','jobs','list','--location=us-central1','--filter=labels.trial_id=gpu36-exposure02');vms=gc('compute','instances','list','--filter=labels.trial_id=gpu36-exposure02');r=subprocess.run([G,'storage','ls','--recursive','gs://'+BUCKET+'/density36/exposure-pilot02/'],capture_output=True,text=True);assert r.returncode==0,r.stderr
names=[s.rsplit('/',1)[-1] for s in r.stdout.splitlines() if s.startswith('gs://')];report=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow_state=status['state'],jobs=[dict(name=j['name'],state=j['status']['state'],runDuration=j['status'].get('runDuration')) for j in jobs],instances=[dict(name=v['name'],state=v['status']) for v in vms],optimizer_replay_artifact_present='optimizer-replay.json' in names,completed_epoch_checkpoint_names=[n for n in names if '-epoch' in n and n.endswith('.pt')],selection_freeze_present='selection-freeze.json' in names,complete_present='complete.json' in names,error_artifacts=[n for n in names if 'error' in n or n=='partial.json'])
save('results/exposure-pilot02-progress.json',report);print(json.dumps(report))
if 'optimizer-replay.json' in names and not (R/'results/exposure-pilot02-optimizer-replay.json').exists():
 dest=R/'results/exposure-pilot02-optimizer-replay.json';subprocess.run([G,'storage','cp','gs://'+BUCKET+'/density36/exposure-pilot02/optimizer-replay.json',str(dest)],check=True,capture_output=True);assert json.loads(dest.read_text())['passed'];print('Real nonempty-optimizer 32-step replay PASSED for both arms')
