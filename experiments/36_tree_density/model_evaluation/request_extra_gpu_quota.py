"""User-authorized renewed quota request: three total GPUs, no compute launch."""
from pathlib import Path
import json,subprocess,datetime
R=Path(__file__).resolve().parents[1]
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud'
P='tmrw-wildfire-20261015'
OUT=R/'results/extra-two-gpu-request.json'
def run(args):
 p=subprocess.run([G,*args],capture_output=True,text=True)
 return dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
def main():
 if OUT.exists():raise SystemExit('Request record exists; inspect instead of resubmitting')
 email=subprocess.check_output([G,'config','get-value','account'],text=True).strip()
 before=run(['beta','quotas','preferences','list','--project='+P,'--billing-project='+P,'--format=json'])
 assert before['returncode']==0,before
 report=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),requested_total=3,additional_to_existing=2,before=json.loads(before['stdout']),requests={})
 justification='Requesting a smaller increase from 1 to 3 total GPUs (2 additional), following denial of 4 total. This project has completed bounded L4 surrogate-model training runs. Additional capacity is for independent plain/gated model comparisons using private simulation data. Jobs use explicit cloud deadlines, zero automatic retries, checkpoint preservation, cleanup and a cumulative USD125 experiment budget. No capacity is launched by this quota request.'
 for label,ident,quota,extra in [('global','372adac7-559a-4615-b3df-079a62ad6c89','GPUS-ALL-REGIONS-per-project',[]),('regional','density36-l4-four','NVIDIA-L4-GPUS-per-project-region',['--dimensions=region=us-central1'])]:
  report['pending']=label;OUT.write_text(json.dumps(report,indent=2)+'\n')
  result=run(['beta','quotas','preferences','update',ident,'--preferred-value=3','--quota-id='+quota,'--service=compute.googleapis.com','--project='+P,'--billing-project='+P,'--email='+email,'--justification='+justification,'--format=json',*extra])
  report['requests'][label]=result;report.pop('pending');OUT.write_text(json.dumps(report,indent=2)+'\n')
  print(label,result['returncode'],result['stdout'] or result['stderr'],flush=True)
  if result['returncode']!=0:raise SystemExit('Request failed; inspect before further action')
if __name__=='__main__':main()
