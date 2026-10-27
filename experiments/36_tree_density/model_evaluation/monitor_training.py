"""Read only execution and artifact progress; never submit or inspect test outcomes."""
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,read,gc,save
execution=read('results/model-training-execution.json')['name'].split('/')
s=gc('workflows','executions','describe',execution[-1],'--workflow='+execution[-3],'--location=us-central1')
p=subprocess.run([G,'storage','ls','gs://'+BUCKET+'/density36/model-training01/'],capture_output=True,text=True,check=True)
names=[x.rsplit('/',1)[-1] for x in p.stdout.splitlines()]
progress={}
for i in range(10):
 prefix=f'fold{i:02}-epoch';epochs=[int(n[len(prefix):len(prefix)+3]) for n in names if n.startswith(prefix) and n.endswith('.pt')]
 progress[str(i)]={'last_checkpoint_epoch':max(epochs,default=0),'selected':f'fold{i:02}-selected.pt' in names,'checkpoint_replay_verified_artifact':f'fold{i:02}-checkpoint-replay.json' in names}
r={'workflow_state':s['state'],'execution':s['name'],'folds':progress,'selection_freeze_present':'selection-freeze.json' in names,'complete_present':'complete.json' in names,'bootstrap_error_present':'bootstrap-error.txt' in names,'test_outcomes_not_read':True}
save('results/model-training-progress.json',r);print(json.dumps(r))
