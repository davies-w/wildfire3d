"""Launch only the approved nine-case recovery; never restart the cloud parent."""
import argparse,base64,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from cloud import R,B,G,PROJECT,BUCKET,gc,read

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--proof',default='results/partial-recovery-workflow.json');args=ap.parse_args()
 proof=read(args.proof);name=proof['group'];folder=R/'jobs'/name
 package=R/proof.get('package_file','data/partial-recovery/'+name+'.xz');workflow=R/proof.get('workflow_file','jobs/'+name+'/workflow.yaml')
 assert proof['only_identity_and_package_hash_changed'] and 0<len(proof['cases'])<=12 and not set(proof['cases'])&set(proof['excluded_completed_cases'])
 assert hashlib.sha256(package.read_bytes()).hexdigest()==proof['package_sha256']
 assert hashlib.sha256(workflow.read_bytes()).hexdigest()==proof['workflow_sha256']
 assert read('results/overnight-authorization.json')['approved']
 assert not (folder/'execution.json').exists(),'Already submitted; inspect existing execution'
 intents=subprocess.run([G,'storage','ls','gs://'+BUCKET+'/density36/orchestration/intents/*.json'],check=True,capture_output=True,text=True).stdout.splitlines()
 expected={f'x36-density-{i:03d}.json' for i in range(29,131)}
 assert expected<={x.rsplit('/',1)[-1] for x in intents},'Parent still has unsubmitted groups'
 jobs=gc('batch','jobs','list','--location=us-central1');vms=gc('compute','instances','list')
 assert len(jobs)<20 and len(vms)<20,'Wait for a fully freed worker slot'
 assert not any(name in x['name'] for x in jobs+vms)
 workflows=gc('workflows','list','--location=us-central1')
 exists=any(x['name'].endswith('/fds-'+name) for x in workflows)
 if exists:assert not gc('workflows','executions','list','fds-'+name,'--location=us-central1'),'Existing execution: reconcile unknown outcome, never resubmit'
 gc('artifacts','docker','images','describe',proof['image_uri'])
 print(json.dumps({'ready':True,'jobs':len(jobs),'vms':len(vms),'recovery_cases':proof['cases'],'execute':args.execute}),flush=True)
 if not args.execute:return
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text())
  assert name not in b['reservations'],'Existing reservation requires reconciliation before retry'
  assert b['estimated_spend_usd']+b['reserved_usd']+.4<=125
  b['reservations'][name]={'state':'reserved_before_upload','allowance_usd':.4,'reserved_unix':time.time(),'cases':len(proof['cases']),'scope':'Approved diagnosed recovery of unfinished cases only'}
  b['reserved_usd']+=.4;B.write_text(json.dumps(b,indent=2)+'\n')
 uri='gs://'+BUCKET+'/density36/'+name+'/input.xz'
 probe=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],capture_output=True,text=True)
 if probe.returncode:
  assert '404' in probe.stderr or 'not found' in probe.stderr.lower(),probe.stderr
  subprocess.run([G,'storage','cp',str(package),uri,'--if-generation-match=0'],check=True,capture_output=True,timeout=240)
 meta=gc('storage','objects','describe',uri)
 assert meta['md5_hash']==base64.b64encode(hashlib.md5(package.read_bytes()).digest()).decode()
 (folder/'input-upload.json').write_text(json.dumps(meta,indent=2)+'\n')
 # Reuse the existing time-limited campaign prefix permission; no new IAM grant.
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
 gc('workflows','deploy','fds-'+name,'--location=us-central1','--source='+str(workflow),'--service-account='+sa)
 assert yaml.safe_load(gc('workflows','describe','fds-'+name,'--location=us-central1')['sourceContents'])==yaml.safe_load(workflow.read_text())
 assert not gc('workflows','executions','list','fds-'+name,'--location=us-central1')
 assert len(gc('batch','jobs','list','--location=us-central1'))<20 and len(gc('compute','instances','list'))<20
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][name]['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 # No retry around paid execution. Any ambiguous outcome remains submission_pending.
 execution=gc('workflows','execute','fds-'+name,'--location=us-central1')
 (folder/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
 (R/('results/partial-recovery-execution.json' if name=='x36-density-032-r1' else 'results/'+name+'-execution.json')).write_text(json.dumps({'group':name,'cases':proof['cases'],'execution':execution,'allowance_usd':.4,'uses_existing_campaign_read_permission':True},indent=2)+'\n')
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());b['reservations'][name].update(state='submitted',execution=execution['name']);B.write_text(json.dumps(b,indent=2)+'\n')
 print('SUBMITTED',execution['name'],flush=True)
if __name__=='__main__':main()
