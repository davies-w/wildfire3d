"""Archive exact diagnosed startup failure, audit resources/cost and close pool01."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64,shutil,torch
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'));from cloud import gc,G,BUCKET
O=R/'results';D=R/'data/failed-pool01';D.mkdir(exist_ok=True)
p=json.loads((O/'package.json').read_text());e=json.loads((O/'execution.json').read_text())['name'];s=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1');assert s['state']=='SUCCEEDED' and json.loads(s['result'])['batch_state']=='FAILED'
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o'
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=180)
with get(base+'?'+urllib.parse.urlencode(dict(prefix=p['prefix'],maxResults=1000))) as f:ls=json.load(f)
assert not ls.get('nextPageToken');proof={}
for m in ls.get('items',[]):
 n=m['name'][len(p['prefix']):];dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True)
 if n=='inputs.tar':shutil.copy2(R/'data/training/inputs.tar',dest)
 elif not dest.exists():
  with get(base+'/'+urllib.parse.quote(m['name'],safe='')+'?'+urllib.parse.urlencode(dict(alt='media',generation=m['generation']))) as f:dest.write_bytes(f.read())
 b=dest.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'];proof[n]=dict(metadata=m,sha256=hashlib.sha256(b).hexdigest())
assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
assert 'cudnn RNN backward can only be called in training mode' in (D/'ia/bootstrap-error.txt').read_text()
assert not any('epoch160' in n for n in proof)
for n in ['optimizer-resume-check.json','resumed-checkpoint-replay.json','timing-check.json']:assert json.loads((D/'ia'/n).read_text())['passed']
ck=torch.load(R/'data/training/data/resume/fold00.pt',map_location='cpu',weights_only=False);assert ck['epoch']==159 and ck['optimizer']['state'] and ck['rng'];assert hashlib.sha256((R/'data/training/data/resume/fold00.pt').read_bytes()).hexdigest()==p['resume_sha256']
(O/'failure-audit.json').write_text(json.dumps(dict(passed=True,reason='Startup deterministic backward used cuDNN GRU eval mode',last_completed_epoch=159,no_new_training_epoch=True,actual_dropout_backward_and_optimizer_replay_passed=True,objects=proof),indent=2)+'\n')
# Reuse exact allocation audit/grant cleanup, but require the diagnosed failed outcome.
src=subprocess.check_output(['git','show','911458312fdc4eb96aea34b9ae9c6f8abfc05e22:experiments/40_dropout10_continuation/close.py'],text=True).replace("assert json.loads((O/'collected.json').read_text())['passed']","assert json.loads((O/'failure-audit.json').read_text())['passed']").replace("['batch_state']=='SUCCEEDED'","['batch_state']=='FAILED'").replace("state='completed_closed'","state='startup_failure_closed'").replace("reason='Batch succeeded and all selected/epoch artifacts verified'","reason='Archived diagnosed pre-training cuDNN mode check failure'")
exec(compile(src,str(R/'close.py'),'exec'))
