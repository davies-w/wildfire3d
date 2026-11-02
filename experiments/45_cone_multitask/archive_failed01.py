"""Archive diagnosed pre-ownership controller failure and audit exact pool cleanup/cost."""
from pathlib import Path
import sys,json,subprocess,urllib.parse,hashlib,base64,shutil,requests
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'));from cloud import gc,G,BUCKET
O=R/'results';D=R/'data/failed-pool01';D.mkdir(exist_ok=True)
p=json.loads((O/'package.json').read_text());e=json.loads((O/'execution.json').read_text())['name'];state=gc('workflows','executions','describe',e.rsplit('/',1)[-1],'--workflow='+p['workflow'],'--location=us-central1');assert state['state']=='FAILED'
s=requests.Session();s.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip();base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o'
x=s.get(base,params=dict(prefix=p['prefix'],maxResults=1000),timeout=60);x.raise_for_status();ls=x.json();assert not ls.get('nextPageToken');proof={}
for m in ls.get('items',[]):
 n=m['name'][len(p['prefix']):];dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True)
 if n=='inputs.tar':
  if not dest.exists():
   import os
   os.link(R/'data/training/inputs.tar',dest)
 elif not dest.exists():
  q=s.get(base+'/'+urllib.parse.quote(m['name'],safe=''),params=dict(alt='media',generation=m['generation']),timeout=90);q.raise_for_status();dest.write_bytes(q.content)
 b=dest.read_bytes();assert len(b)==int(m['size']) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'];proof[n]=dict(metadata=m,sha256=hashlib.sha256(b).hexdigest())
assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
failure=json.loads((D/'controller-error.json').read_text());assert failure['tags']==['ConnectionError'] and failure['message']=='connection broken'
assert 'race-winner.json' not in proof, 'Ownership existed; requires a different audit'
assert not any('fold00-epoch' in n for n in proof)
(O/'failure-audit.json').write_text(json.dumps(dict(passed=True,reason='Controller ConnectionError before ownership; no optimizer work permitted or completed epochs',no_completed_epochs=True,objects=proof),indent=2)+'\n')
src=(R/'close01.py').read_text().replace("assert json.loads((O/'collected.json').read_text())['passed']","assert json.loads((O/'failure-audit.json').read_text())['passed']").replace("assert state['state']=='SUCCEEDED'","assert state['state']=='FAILED'").replace("assert json.loads(state['result'])['batch_state']=='SUCCEEDED'","assert 'ConnectionError' in state['error']['payload']").replace("state='completed_closed'","state='startup_failure_closed'").replace("reason='Batch succeeded and all selected/epoch artifacts verified'","reason='Archived pre-ownership transient controller connection failure'")
exec(compile(src,str(R/'close01.py'),'exec'))
