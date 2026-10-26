"""Predeploy immutable inputs and child workflows; never executes paid jobs."""
from pathlib import Path
import sys,json,subprocess,concurrent.futures,base64,hashlib,yaml
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R));from cloud import gc,G,PROJECT,BUCKET
O=R/'orchestration';SA='fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com'
def run(args):
 p=subprocess.run([G,*args],capture_output=True,text=True,timeout=300)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout
for who in ['fds-worker','fds-watchdog']:
 run(['storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+who+'@'+PROJECT+'.iam.gserviceaccount.com','--role=roles/storage.objectViewer','--condition-from-file='+str(O/'read-condition.json')])
# Inline parent uses existing watchdog Batch permissions; no workflow invoker grant.
def upload(path,uri):
 p=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],capture_output=True,text=True)
 if p.returncode:
  assert '404' in p.stderr or 'not found' in p.stderr.lower(),p.stderr
  run(['storage','cp',str(path),uri,'--if-generation-match=0'])
 m=gc('storage','objects','describe',uri);assert m['md5_hash']==base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode()
 return m
upload(O/'run-queue.json','gs://'+BUCKET+'/density36/orchestration/run-queue.json')
gc('workflows','deploy','fds-density36-parent','--location=us-central1','--source='+str(O/'parent-inline.yaml'),'--service-account='+SA)
def one(g):
 n=g['id'];f=R/'jobs'/n;p=O/(n+'-deployed.json')
 if p.exists():return
 assert not (f/'execution.json').exists()
 assert not gc('workflows','executions','list','fds-'+n,'--location=us-central1') if (O/(n+'-deploy-started.json')).exists() else True
 package=R/g.get('package_file','data/packages/'+n+'.xz')
 meta=upload(package,'gs://'+BUCKET+'/density36/'+n+'/input.xz')
 (f/'input-upload.json').write_text(json.dumps(meta,indent=2)+'\n')
 w=f/g['workflow_file'];assert hashlib.sha256(w.read_bytes()).hexdigest()==g['workflow_sha256']
 gc('workflows','deploy','fds-'+n,'--location=us-central1','--source='+str(w),'--service-account='+SA)
 assert yaml.safe_load(gc('workflows','describe','fds-'+n,'--location=us-central1')['sourceContents'])==yaml.safe_load(w.read_text())
 assert not gc('workflows','executions','list','fds-'+n,'--location=us-central1')
 p.write_text(json.dumps({'deployed':True,'workflow_sha256':g['workflow_sha256'],'package_sha256':g['package_sha256']},indent=2)+'\n');print('PREDEPLOYED',n,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,json.loads((O/'queue.json').read_text())))
(O/'deployment-complete.json').write_text(json.dumps({'groups':102,'no_executions_created':True},indent=2)+'\n')
