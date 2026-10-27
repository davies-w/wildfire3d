"""Immutable private upload and no-GPU cloud validation; never starts training."""
from pathlib import Path
import sys,json,hashlib,base64,subprocess,datetime,time,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,PROJECT,BUCKET,gc,read,save
D=R/'data/flex-queue';WF='fds-gpu36-flex-queue01'
def main():
 assert not (R/'results/flex-queue-execution.json').exists()
 p=read('results/flex-queue-prepared.json');assert hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest()==p['workflow_sha256']
 inv={k:gc(*v) for k,v in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()};assert not any(inv.values());save('results/flex-queue-empty-inventory.json',inv)
 regional={q['metric']:q['limit']-q['usage'] for q in gc('compute','regions','describe','us-central1')['quotas']};glob={q['metric']:q['limit']-q['usage'] for q in gc('compute','project-info','describe')['quotas']};assert regional['PREEMPTIBLE_NVIDIA_L4_GPUS']>=1 and regional['PREEMPTIBLE_CPUS']>=4 and glob['GPUS_ALL_REGIONS']>=1
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];uploads={}
 for pkg in p['packages']:
  path=D/f"rotation{pkg['rotation']}"/'inputs.tar';assert hashlib.sha256(path.read_bytes()).hexdigest()==pkg['sha256'];uri='gs://'+BUCKET+'/'+pkg['prefix']+'inputs.tar'
  probe=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],text=True,capture_output=True)
  if probe.returncode:
   assert '404' in probe.stderr or 'not found' in probe.stderr.lower(),probe.stderr
   subprocess.run([G,'storage','cp','--if-generation-match=0',str(path),uri],check=True,capture_output=True)
  m=gc('storage','objects','describe',uri);assert int(m['size'])==path.stat().st_size and m['md5_hash']==base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode();uploads[uri]=m
 save('results/flex-queue-uploads.json',uploads)
 cpath=R/'results/flex-queue-read-condition.json'
 if cpath.exists():c=json.loads(cpath.read_text())
 else:
  expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=20)).strftime('%Y-%m-%dT%H:%M:%SZ');c=dict(title='density36-flex-queue01-read',description='Private inputs and verification for bounded fixed-order Flex-start queue',expression="request.time < timestamp('"+expiry+"') && resource.name.startsWith('projects/_/buckets/"+BUCKET+"/objects/"+p['prefix']+"')");save(str(cpath.relative_to(R)),c)
 for member in ('fds-worker@'+PROJECT+'.iam.gserviceaccount.com',sa.split('/')[-1]):subprocess.run([G,'storage','buckets','add-iam-policy-binding','gs://'+BUCKET,'--member=serviceAccount:'+member,'--role=roles/storage.objectViewer','--condition-from-file='+str(cpath)],check=True,capture_output=True)
 # Validate all zones' instance/disk listing plus input read and mixed JSON decoding in cloud.
 w=yaml.safe_load((D/'workflow.yaml').read_text());check=yaml.safe_load((D/'readiness.yaml').read_text());check['decode_document']=w['decode_document']
 check['main']['steps'][-1:-1]=[{'input':{'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/density36%2Fflex-queue01%2Frotation1%2Finputs.tar','auth':{'type':'OAuth2'}},'result':'input_meta'}},{'decode_text':{'call':'decode_document','args':{'value':'{"success":true,"folds":2}'},'result':'decoded'}},{'decode_map':{'call':'decode_document','args':{'value':'${decoded}'},'result':'decoded_again'}},{'assert_decode':{'switch':[{'condition':'${decoded_again.success != true or decoded_again.folds != 2}','raise':'Decode check failed'}]}}]
 (D/'readiness.yaml').write_text(yaml.safe_dump(check,sort_keys=False))
 gc('workflows','deploy',WF+'-check','--location=us-central1','--source='+str(D/'readiness.yaml'),'--service-account='+sa)
 e=gc('workflows','execute',WF+'-check','--location=us-central1');save('results/flex-queue-readiness-execution.json',e)
 for _ in range(30):
  q=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF+'-check','--location=us-central1')
  if q['state']!='ACTIVE':break
  time.sleep(2)
 save('results/flex-queue-readiness.json',q);assert q['state']=='SUCCEEDED',q
 gc('workflows','deploy',WF,'--location=us-central1','--source='+str(D/'workflow.yaml'),'--service-account='+sa)
 deployed=gc('workflows','describe',WF,'--location=us-central1');assert yaml.safe_load(deployed['sourceContents'])==w;assert not gc('workflows','executions','list',WF,'--location=us-central1');save('results/flex-queue-deployed.json',deployed)
 print('Prepared and cloud-validated; NO training submission')
if __name__=='__main__':main()
