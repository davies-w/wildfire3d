"""Point monitoring/preservation at the repaired unique pool; no submission."""
from pathlib import Path
import json,yaml,shutil
R=Path(__file__).resolve().parent
assert json.loads((R/'results/pool-closed.json').read_text())['passed']
assert json.loads((R/'validation02.json').read_text())['passed']
assert not (R/'results02/submission-intent.json').exists()
for name in ['monitor.py','fetch_progress.py','audit_startup.py','collect.py','close.py']:
 p=R/name;old=R/(p.stem+'01.py');assert not old.exists();shutil.copy2(p,old)
 p.write_text(p.read_text().replace("R/'results'","R/'results02'").replace('results/','results02/').replace('pool01','pool02').replace('data/training/','data/training02/'))
p=R/'archive_failed01.py';p.write_text(p.read_text().replace("R/'close.py'","R/'close01.py'"))
p=R/'snapshot_progress.py';p.write_text(p.read_text().replace("R/'results'","R/'results02'"))
p=R/'preserve.py';s=p.read_text();s+= "\nshutil.copytree(R/'results02',D/'results02',dirs_exist_ok=True)\nshutil.copytree(R/'data/failed-pool01',D/'failed-pool01',dirs_exist_ok=True)\n";p.write_text(s)
p=R/'push_artifacts.py';s=p.read_text().replace("['prepare','progress'","['prepare','prepare_pool02','progress'").replace("default='prepare'","default='prepare_pool02'").replace('data/training/','data/training02/').replace("R/'data/training'","R/'data/training02'").replace("args.stage in ['prepare']","args.stage in ['prepare','prepare_pool02']");p.write_text(s)
p=R/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['prepare_pool02']={'cmd':'../../.venv/bin/python prepare_pool02.py','deps':['prepare_pool02.py','build_pool02.py','gated_model02.py','cloud_check.py','data/training'],'outs':[{'data/training02':{'persist':True}}]};d['stages']['collect']['outs']=[{'data/pool02-results':{'persist':True}}];p.write_text(yaml.safe_dump(d,sort_keys=False))
p=R/'.gitignore';p.write_text(p.read_text()+'/results02/\n')
print('Operational tools now target pool02; pool01 preserved and closed')
