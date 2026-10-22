"""Generate a bounded controller using the previously tested cleanup workflow."""
from pathlib import Path
import yaml,json,base64
ROOT=Path(__file__).resolve().parent
p=ROOT.parent/'16_code_profiling/workflow.yaml';w=yaml.safe_load(p.read_text());steps=w['main']['steps']
a=steps[0]['initialize']['assign'];a[0]['deadline']='${sys.now() + 10800}';job=a[1]['job'];spec=job['taskGroups'][0]['taskSpec'];spec['maxRunDuration']='10380s'
paths=[ROOT/n for n in ['generate.py','runner.py','worker.py']]+list((ROOT/'inputs').glob('*'))
payload={str(p.relative_to(ROOT)):base64.b64encode(p.read_bytes()).decode() for p in paths}
bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
spec['runnables'][0]['container']['commands']=['-c',bootstrap]
job['allocationPolicy']['labels']['trial_id']='study17';job['labels']['trial_id']='study17'
# Replace only human-readable workflow fields, never the encoded input payload.
for step in steps:
    if 'record' in step:step['record']['try']['args']['query']['name']='domain17/job-status.json'
    for k in ['list_workers','verify']:
        if k in step:step[k]['args']['query']['filter']='labels.trial_id = study17'
    if 'done' in step:step['done']['return']['mode']='domain17'
(ROOT/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(ROOT/'job.json').write_text(json.dumps(job,indent=2)+'\n')
(ROOT/'estimate.json').write_text(json.dumps(dict(estimated_total_usd=.30,conservative_allowance_usd=.40,worker_deadline_seconds=10800,c3_spot_hourly_usd=.065744,max_compute_usd=.197232,ancillary_allowance_usd=.10,builds=0,max_jobs=1,max_retries=0,source='https://cloud.google.com/spot-vms/pricing?hl=en',invoice_confirmed=False),indent=2)+'\n')
