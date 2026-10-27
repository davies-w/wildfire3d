"""Explicitly requested Flex-start quota increase; does not allocate compute."""
from pathlib import Path
import json,subprocess,datetime
R=Path(__file__).resolve().parents[1];G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';P='tmrw-wildfire-20261015';OUT=R/'results/flex-quota-request.json'
def run(args):
 p=subprocess.run([G,*args,'--project='+P,'--billing-project='+P,'--format=json'],text=True,capture_output=True,timeout=180)
 return dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
def main():
 assert not OUT.exists(),'Inspect existing request; never duplicate an unknown outcome'
 before=run(['beta','quotas','preferences','list']);assert before['returncode']==0
 preferences=json.loads(before['stdout'])
 email=subprocess.check_output([G,'config','get-value','account'],text=True).strip()
 reason='Requesting quota specifically for Google Batch FLEX_START, using preemptible L4 quota rather than standard provisioning. Delay-tolerant scientific surrogate training accepts a 24-hour allocation wait. Request 4 L4 GPUs and 16 preemptible vCPUs in us-central1; fixed grouped folds run independent matched plain/gated models. Every run has cloud supervision, immutable checkpoints, bounded duration, zero automatic paid retries and cleanup. Total experiment spending is capped at USD125. Actual concurrency is subject to budget and granted quota. Prior standard GPU increases were denied; this request concerns the separate preemptible quota used by Flex-start.'
 report=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='User-authorized Flex-start Batch capacity',before=preferences,requests={})
 items=[('l4','density36-flex-l4-4','PREEMPTIBLE-NVIDIA-L4-GPUS-per-project-region',4),('cpu','density36-flex-cpus-16','PREEMPTIBLE-CPUS-per-project-region',16)]
 for label,ident,quota,value in items:
  assert not any(x['name'].endswith('/'+ident) for x in preferences)
  info=run(['beta','quotas','info','describe',quota,'--service=compute.googleapis.com']);assert info['returncode']==0,info
  report['pending']=label;report[label+'_definition']=json.loads(info['stdout']);OUT.write_text(json.dumps(report,indent=2)+'\n')
  result=run(['beta','quotas','preferences','create','--preference-id='+ident,'--preferred-value='+str(value),'--quota-id='+quota,'--service=compute.googleapis.com','--dimensions=region=us-central1','--email='+email,'--justification='+reason])
  report['requests'][label]=result;report.pop('pending');OUT.write_text(json.dumps(report,indent=2)+'\n');print(label,result['returncode'],result['stdout'] or result['stderr'],flush=True)
  if result['returncode']:raise SystemExit('Request failed; inspect before retry')
if __name__=='__main__':main()
