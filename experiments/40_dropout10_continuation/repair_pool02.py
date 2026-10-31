"""Prepare unique pool02; fix startup probe only, preserving failed pool01 inputs."""
from pathlib import Path
import shutil,subprocess,sys,yaml
R=Path(__file__).resolve().parent;O=R/'results02';O.mkdir(exist_ok=True)
assert not (O/'submission-intent.json').exists()
D=R/'data/training02';shutil.copytree(R/'data/training',D,dirs_exist_ok=True)
p=D/'worker.py';s=p.read_text();assert 'm=Transition(kind).to(device);m.eval()' in s
s=s.replace('m=Transition(kind).to(device);m.eval()','m=Transition(kind).to(device);m.train();m.shared[-1].eval()').replace('m2=Transition(kind).to(device);m2.eval();','m2=Transition(kind).to(device);m2.train();m2.shared[-1].eval();').replace('evaluation_dropout_disabled','training_gru_dropout_disabled')
p.write_text(s)
# Leave the GRU in train mode for cuDNN backward, disable only dropout in this
# deterministic serialization/gradient check. Actual training probes retain dropout.
s=(R/'build_pool.py').read_text().replace("D=R/'data/training'; O=R/'results'","D=R/'data/training02'; O=R/'results02'").replace('pool01','pool02').replace('readiness01','readiness02')
s=s.replace('49500','45900').replace('48600','45000').replace('50400','46800').replace('11.2','10.45')
s=s.replace(".replace('[(64,20),(90,271)]','[(90,241)]')", ".replace('[(64,20),(90,271)]','[(90,241)]').replace('48600','45000')")
(R/'build_pool02.py').write_text(s)
subprocess.run([sys.executable,str(R/'build_pool02.py')],check=True)
s=(R/'launch.py').read_text().replace("O=R/'results';D=R/'data/training'","O=R/'results02';D=R/'data/training02'").replace('pool01','pool02').replace("(R.parent/'39_long_window_continuation/results02/pool-closed.json')","(R/'results/pool-closed.json')").replace('14h VM max','13h VM max')
(R/'launch02.py').write_text(s)
s=(R/'deploy.py').read_text().replace("results/submission-intent.json","results02/submission-intent.json").replace('pool01','pool02').replace('readiness01','readiness02');(R/'deploy02.py').write_text(s)
for name in ['monitor.py','fetch_progress.py','audit_startup.py','collect.py','close.py']:
 p=R/name;s=p.read_text().replace("R/'results'","R/'results02'").replace('results/','results02/').replace('pool01','pool02').replace('data/training/','data/training02/');p.write_text(s)
s=(R/'validate.py').read_text().replace("D=R/'data/training'","D=R/'data/training02'").replace('pool01.yaml','pool02.yaml').replace("(R/'validation.json')","(R/'validation02.json')")
s=s.replace("proof=dict(","assert 'm.train();m.shared[-1].eval()' in (D/'worker.py').read_text()\nassert 'm2.train();m2.shared[-1].eval()' in (D/'worker.py').read_text()\nproof=dict(")
(R/'validate02.py').write_text(s)
p=R/'push_artifacts.py';s=p.read_text().replace("['prepare','progress','collect']","['prepare','prepare_pool02','progress','collect']").replace("default='prepare'","default='prepare_pool02'").replace('data/training/','data/training02/').replace("(R/'data/training')","(R/'data/training02')").replace("args.stage=='prepare'","args.stage in ['prepare','prepare_pool02']");p.write_text(s)
p=R/'snapshot_progress.py';p.write_text(p.read_text().replace("R/'results'","R/'results02'"))
p=R/'preserve.py';s=p.read_text();s=s.replace("shutil.copytree(R/'results',D/'results',dirs_exist_ok=True)\nshutil.copytree(R/'results',D/'results',dirs_exist_ok=True)","shutil.copytree(R/'results',D/'results',dirs_exist_ok=True)\nshutil.copytree(R/'results02',D/'results02',dirs_exist_ok=True)\nshutil.copytree(R/'data/failed-pool01',D/'failed-pool01',dirs_exist_ok=True)");p.write_text(s)
p=R/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['prepare_pool02']={'cmd':'../../.venv/bin/python repair_pool02.py','deps':['repair_pool02.py','build_pool.py','launch.py','deploy.py','data/training'],'outs':[{'data/training02':{'persist':True}}]};d['stages']['collect']['outs']=[{'data/pool02-results':{'persist':True}}];p.write_text(yaml.safe_dump(d,sort_keys=False))
p=R/'.gitignore';p.write_text(p.read_text()+'/results02/\n')
print('Prepared repaired unique pool02. No submission executed.')
