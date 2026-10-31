"""Retarget operational tools after verified preemption closure; never launch."""
from pathlib import Path
import json,shutil,yaml
R=Path(__file__).resolve().parent
assert json.loads((R/'results02/pool-closed.json').read_text())['passed']
assert json.loads((R/'results03/continuation-validation.json').read_text())['passed']
assert not (R/'results03/submission-intent.json').exists()
for n in ['monitor.py','fetch_progress.py','audit_startup.py','collect.py','close.py']:
 p=R/n;old=R/(p.stem+'02.py');assert not old.exists();shutil.copy2(p,old)
 s=p.read_text().replace('results02','results03').replace('pool02','pool03').replace('training02','training03')
 if n=='audit_startup.py':s=s.replace('fresh-initialization-replay.json','resumed-checkpoint-replay.json').replace('actual first-epoch proof; no inherited epochs','exact resumed epoch31 proof and inherited original epoch1 proof')
 p.write_text(s)
p=R/'snapshot_progress.py';p.write_text(p.read_text().replace('results02','results03'))
p=R/'preserve.py';s=p.read_text()+"\nshutil.copytree(R/'results03',D/'results03',dirs_exist_ok=True)\nshutil.copytree(R/'data/preempted02',D/'preempted02',dirs_exist_ok=True)\n";p.write_text(s)
p=R/'push_artifacts.py';s=p.read_text().replace("'prepare_pool02','progress'","'prepare_pool02','prepare_pool03','progress'").replace("default='prepare_pool02'","default='prepare_pool03'").replace('training02','training03').replace("args.stage in ['prepare','prepare_pool02']","args.stage in ['prepare','prepare_pool02','prepare_pool03']");p.write_text(s)
p=R/'track_artifacts.py';p.write_text(p.read_text().replace('results02/collected','results03/collected'))
p=R/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['prepare_pool03']={'cmd':'../../.venv/bin/python prepare_pool03.py','deps':['prepare_pool03.py','build_pool03.py','cloud_check03.py','data/training02'],'outs':[{'data/training03':{'persist':True}}]};d['stages']['collect']['outs']=[{'data/pool03-results':{'persist':True}}];p.write_text(yaml.safe_dump(d,sort_keys=False))
p=R/'.gitignore';p.write_text(p.read_text()+'/results03/\n')
print('Operational tools target pool03')
