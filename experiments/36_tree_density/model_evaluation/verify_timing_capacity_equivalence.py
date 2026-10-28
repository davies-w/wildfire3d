"""Prove a placement/hardware alternative preserves timing01's scientific payload."""
from pathlib import Path
import argparse,base64,hashlib,json,yaml
R=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pilot',required=True,choices=['02','03','04','05']);ap.add_argument('--zone',required=True);ap.add_argument('--batch-region',default='us-central1');ap.add_argument('--subnet',default='fds-trial');ap.add_argument('--hardware',choices=['l4','t4'],default='l4');args=ap.parse_args();pilot=args.pilot
 a=R/'data/timing-decoder-pilot01';b=R/('data/timing-decoder-pilot'+pilot);pa=json.loads((R/'results/timing-decoder-pilot01-prepared.json').read_text());pb=json.loads((R/('results/timing-decoder-pilot'+pilot+'-prepared.json')).read_text());changed=[n for n in pa['files'] if pa['files'][n]!=pb['files'][n]];assert set(pa['files'])==set(pb['files'])
 assert set(changed)<= {'runtime.py','trial-plan.json'} and 'runtime.py' in changed
 old='timing-decoder-pilot01';new='timing-decoder-pilot'+pilot
 assert (a/'runtime.py').read_text().replace(old,new)==(b/'runtime.py').read_text()
 for folder,prepared in [(a,pa),(b,pb)]:
  for name,h in prepared['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h
  assert hashlib.sha256((folder/'workflow.yaml').read_bytes()).hexdigest()==prepared['workflow_sha256']
 plan_a=json.loads((a/'trial-plan.json').read_text());plan_b=json.loads((b/'trial-plan.json').read_text());ba=plan_a.pop('budget_plan');bb=plan_b.pop('budget_plan');assert plan_a==plan_b
 for key in ba:
  if key not in ['maximum_allowance_usd','maximum_rate_bound_usd_per_hour']:assert ba[key]==bb[key],key
 assert (bb['vm_creation_age_cap_s']+bb['shutdown_margin_s'])*bb['maximum_rate_bound_usd_per_hour']/3600<=bb['maximum_allowance_usd']
 wa=yaml.safe_load((a/'workflow.yaml').read_text());wb=yaml.safe_load((b/'workflow.yaml').read_text())
 for folder,w in [(a,wa),(b,wb)]:
  task=w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec'];expected="import base64;exec(compile(base64.b64decode("+repr(base64.b64encode((folder/'bootstrap.py').read_bytes()).decode())+"),'bootstrap','exec'))";assert task['runnables'][0]['container']['commands']==['-c',expected];task['runnables'][0]['container']['commands']=['verified bootstrap']
 if args.hardware=='t4':
  policy=wa['main']['steps'][0]['initialize']['assign'][1]['job']['allocationPolicy']['instances'][0]['policy'];policy['machineType']='n1-standard-4';policy['accelerators']=[{'type':'nvidia-tesla-t4','count':1}]
 expected=yaml.safe_dump(wa).replace('gpu36-timing01','gpu36-timing'+pilot).replace(old,new).replace('us-central1-a',args.zone).replace('/locations/us-central1/jobs','/locations/'+args.batch_region+'/jobs').replace('regions/us-central1/subnetworks/fds-trial','regions/'+args.batch_region+'/subnetworks/'+args.subnet)
 assert expected==yaml.safe_dump(wb),'Unexplained workflow change'
 assert (a/'bootstrap.py').read_text().replace(old,new)==(b/'bootstrap.py').read_text()
 p=dict(passed=True,scientific_payload_identical=True,changed_archive_members=changed,workflow_difference_verified=True,bootstrap_difference_verified=True,source_input_sha256=pa['input_sha256'],fallback_input_sha256=pb['input_sha256'],hardware=args.hardware,zone=args.zone,batch_region=args.batch_region,subnet=args.subnet,maximum_allowance_usd=bb['maximum_allowance_usd'],maximum_rate_bound_usd_per_hour=bb['maximum_rate_bound_usd_per_hour'],submitted=False,limitations='Execution namespace, placement/network, optional declared GPU configuration and budget ceilings only. Actual CUDA determinism, speed, completion and accuracy are untested by this check.')
 (R/('results/timing-decoder-pilot'+pilot+'-capacity-equivalence.json')).write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(p,indent=2))
if __name__=='__main__':main()
