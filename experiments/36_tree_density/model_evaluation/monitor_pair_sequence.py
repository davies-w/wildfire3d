"""Read cloud-owned sequence status without opening test outcomes."""
from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
x=read('results/pair-sequence-execution.json')['name'].split('/');state=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');progress={}
for rotation in (0,1):
 p=subprocess.run([G,'storage','ls','gs://'+BUCKET+f'/density36/pair-sequence01/rotation{rotation}/'],capture_output=True,text=True,check=True);names={n.rsplit('/',1)[-1] for n in p.stdout.splitlines()};arms={}
 for i,kind in enumerate(('control','gated')):
  prefix=f'fold{i:02}-epoch';epochs=[int(n[len(prefix):len(prefix)+3]) for n in names if n.startswith(prefix) and n.endswith('.pt')];arms[kind]=dict(checkpoint_epoch=max(epochs,default=0),selected=f'fold{i:02}-selected.pt' in names,replay_proof=f'fold{i:02}-checkpoint-replay.json' in names)
 progress[str(rotation)]=dict(arms=arms,synthetic_resume_proof='optimizer-resume-check.json' in names,complete='complete.json' in names,error='bootstrap-error.txt' in names)
continuation=None
if (R/'results/pair-rotation1-execution.json').exists():
 y=read('results/pair-rotation1-execution.json')['name'].split('/');continuation=gc('workflows','executions','describe',y[-1],'--workflow='+y[-3],'--location=us-central1')['state']
r=dict(rotation1_continuation_state=continuation,workflow_state=state['state'],execution=state['name'],rotations=progress,test_outcomes_not_read=True);save('results/pair-sequence-progress.json',r);print(json.dumps(r))
