"""Stop only the exact still-unallocated capacity-rejected comparison; preserve metadata."""
from pathlib import Path
import argparse,datetime,json,sys,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,G,BUCKET,gc,read,save
stem='guard-matched-pilot02';label='gpu36-guardmatch02';x=read('results/'+stem+'-execution.json')['name'].split('/')
ap=argparse.ArgumentParser();ap.add_argument('--finish-deletion',action='store_true');args=ap.parse_args()
if args.finish_deletion:
 terminal=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert terminal['state']=='CANCELLED'
 proof=read('results/'+stem+'-early-capacity-stop.json');job=gc('batch','jobs','describe',proof['job_before_deletion']['name'].split('/')[-1],'--location=us-east4');assert job['uid']==proof['job_before_deletion']['uid']
 gc('batch','jobs','delete',job['name'].split('/')[-1],'--location=us-east4','--quiet');print('Exact cancelled execution job deleted');raise SystemExit(0)
observation=read('results/'+stem+'-infrastructure-observation.json');assert observation['failed_insert_completions_observed']>=5 and observation['successful_insert_completions_observed']==0
execution=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert execution['state']=='ACTIVE'
jobs=gc('batch','jobs','list','--location=us-east4','--filter=labels.trial_id='+label);assert len(jobs)==1
job=jobs[0];assert job['status']['state']=='SCHEDULED' and job['status']['runDuration']=='0s';assert not gc('compute','instances','list','--filter=labels.trial_id='+label)
proof=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_before=execution,job_before_deletion=job,reason='Five exact-UID stockout insert failures with no successful allocation; stop pending task before a separately diagnosed placement attempt. No training result claimed.')
save('results/'+stem+'-early-capacity-stop.json',proof)
gc('workflows','executions','cancel',x[-1],'--workflow='+x[-3],'--location=us-central1','--quiet')
terminal=gc('workflows','executions','describe',x[-1],'--workflow='+x[-3],'--location=us-central1');assert terminal['state']=='CANCELLED';save('results/'+stem+'-status.json',terminal)
root=R/'data'/f'{stem}-results';root.mkdir(exist_ok=True);(root/'job-status.json').write_text(json.dumps(job,indent=2)+'\n')
subprocess.run([G,'storage','cp','--if-generation-match=0',str(root/'job-status.json'),'gs://'+BUCKET+'/density36/'+stem+'/job-status.json'],check=True,capture_output=True)
gc('batch','jobs','delete',job['name'].split('/')[-1],'--location=us-east4','--quiet')
print('Exact execution cancelled; job metadata preserved; deletion requested. Verify resources and allocation logs before any reservation release or new run.')
