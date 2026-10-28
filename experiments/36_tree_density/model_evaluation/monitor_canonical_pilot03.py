"""Read status and artifact names only; never read validation comparisons mid-run."""
import sys,subprocess,json,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
x=read('results/canonical-pilot03-execution.json')['name'].split('/');status=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');jobs=gc('batch','jobs','list','--location=us-west4','--filter=labels.trial_id=gpu36-canonical03');vms=gc('compute','instances','list','--filter=labels.trial_id=gpu36-canonical03');r=subprocess.run([G,'storage','ls','--recursive','gs://'+BUCKET+'/density36/canonical-pilot03/'],capture_output=True,text=True);assert r.returncode==0,r.stderr
names=[s.rsplit('/',1)[-1] for s in r.stdout.splitlines() if s.startswith('gs://')];report=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow_state=status['state'],jobs=[dict(name=j['name'],state=j['status']['state'],runDuration=j['status'].get('runDuration')) for j in jobs],instances=[dict(name=v['name'],state=v['status']) for v in vms],optimizer_replay_artifact_present='optimizer-replay.json' in names,completed_epoch_checkpoint_names=[n for n in names if '-epoch' in n and n.endswith('.pt')],selection_freeze_present='selection-freeze.json' in names,complete_present='complete.json' in names,error_artifacts=[n for n in names if 'error' in n or n=='incomplete.json' or n.endswith('-partial.pt')])
save('results/canonical-pilot03-progress.json',report);summary={k:v for k,v in report.items() if k!='completed_epoch_checkpoint_names'};summary['epoch_checkpoints_by_arm']={arm:sum(n.startswith(arm+'-epoch') for n in names if n.endswith('.pt')) for arm in ['canonical_half','canonical_full']};print(json.dumps(summary))
if 'optimizer-replay.json' in names and not (R/'results/canonical-pilot03-optimizer-replay.json').exists():
 dest=R/'results/canonical-pilot03-optimizer-replay.json';subprocess.run([G,'storage','cp','gs://'+BUCKET+'/density36/canonical-pilot03/optimizer-replay.json',str(dest)],check=True,capture_output=True);assert json.loads(dest.read_text())['passed'];print('Real head nonempty-optimizer replay PASSED for both arms')

proof_path=R/'results/canonical-pilot03-optimizer-replay.json'
if proof_path.exists():
 proof=read('results/canonical-pilot03-optimizer-replay.json');assert proof['passed'] and 'L4' in proof['device_name'] and proof['threads']==4
 for arm in proof['arms']:
  assert arm['all_five_canonical_windows_in_restore_fixture']
  assert arm['serialized_restore_map_location']=='cpu' and arm['optimizer_device_layout_preserved'] and arm['serialized_checkpoint_restore'] and arm['next_update_bitwise_equal']
  assert arm['optimizer_tensor_device_layout']=={'step':['cpu'],'exp_avg':['cuda:0'],'exp_avg_sq':['cuda:0']}
 print('Actual L4 serialized replay and CPU-step/CUDA-moment placement verified for both arms')
