"""Read infrastructure/boot events only for the exact existing canonical03 execution."""
from pathlib import Path
import datetime,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,gc,read,save
stem='canonical-pilot03';label='gpu36-canonical03';e=read('results/'+stem+'-execution.json')['name'].split('/');execution=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1');jobs=gc('batch','jobs','list','--location=us-west4','--filter=labels.trial_id='+label);vms=gc('compute','instances','list','--filter=labels.trial_id='+label);D=R/'data/canonical-startup03';D.mkdir(exist_ok=True);records=[]
for vm in vms:
 zone=vm['zone'].rsplit('/',1)[-1];serial=gc('compute','instances','get-serial-port-output',vm['name'],'--zone='+zone,'--start=-14000');p=D/(vm['name']+'-serial.json');p.write_text(json.dumps(serial,indent=2)+'\n');selected=[s[:1000] for s in serial.get('contents','').splitlines() if any(k in s.lower() for k in ['nvidia','batch','error','failed','docker','driver','agent'])];records.append(dict(name=vm['name'],zone=zone,status=vm['status'],machine=vm['machineType'].rsplit('/',1)[-1],created=vm.get('creationTimestamp'),serial_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),serial_boot_events=selected))
(D/'execution.json').write_text(json.dumps(execution,indent=2)+'\n');(D/'jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
report=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_name=execution['name'],workflow_state=execution['state'],job_statuses=[j['status'] for j in jobs],instances=records,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Infrastructure/boot snapshot only. RUNNING VM and loaded driver are not evidence that model fitting started, finished or improved accuracy. No model-selection output read; no mutation or resubmission.')
save('results/canonical-pilot03-startup-observation.json',report);print(json.dumps({k:v for k,v in report.items() if k!='instances'},indent=2));print('VM boot snapshots preserved:',len(records))
