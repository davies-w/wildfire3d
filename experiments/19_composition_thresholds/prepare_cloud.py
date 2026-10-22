"""Package a single five-hour Spot campaign; does not deploy or execute."""
import base64
import hashlib
import json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent
w=json.loads((ROOT/'workflow_template.json').read_text())
steps=w['main']['steps']; assignments=steps[0]['initialize']['assign']
assignments[0]['deadline']='${sys.now() + 18000}'
job=assignments[1]['job']; spec=job['taskGroups'][0]['taskSpec']
spec['maxRunDuration']='17640s'
paths=[ROOT/n for n in ('generate.py','runner.py','worker.py','design.json','acquisition.py')]+list((ROOT/'inputs').glob('*'))
payload={str(p.relative_to(ROOT)):base64.b64encode(p.read_bytes()).decode() for p in paths}
bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
spec['runnables'][0]['container']['commands']=['-c',bootstrap]
job['labels']['trial_id']='study19';job['allocationPolicy']['labels']['trial_id']='study19'
for step in steps:
    if 'record' in step:step['record']['try']['args']['query']['name']='composition19/job-status.json'
    for name in ('list_workers','verify'):
        if name in step:step[name]['args']['query']['filter']='labels.trial_id = study19'
    if 'done' in step:step['done']['return']['mode']='composition19'
(ROOT/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
(ROOT/'job.json').write_text(json.dumps(job,indent=2)+'\n')
sources=[p for p in ROOT.iterdir() if p.suffix in ('.py','.json','.yaml','.md') and p.name!='workflow.yaml']
(ROOT/'results/prelaunch-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print('Packaged one Spot job; worker 17100 s, task 17640 s, cleanup controller 18000 s.')
