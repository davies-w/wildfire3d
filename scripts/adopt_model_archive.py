"""Adopt existing remote-training artifacts into explicit DVC stages; never train."""
import json,subprocess,yaml
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'.venv/bin/dvc';e=R/'experiments/33_representation_loss'
b=json.loads((e/'budget.json').read_text());b['authorized_usd']=75;b['authorization']='User increased cumulative cap from $35 to $75; archive code/data/models first, then continue model experimentation';(e/'budget.json').write_text(json.dumps(b,indent=2))
folders=[e]+sorted(e.glob('attempt*'))
for p in folders:
 y=p/'dvc.yaml';doc=yaml.safe_load(y.read_text());rel='../../' if p==e else '../../../';st=doc['stages']
 st['cloud_submit']={'cmd':rel+'.venv/bin/python launch.py','frozen':True,'deps':['launch.py','cloud.py','gpu-workflow.yaml','data/pilot-overlay.tar'],'metrics':[{'results/execution.json':{'cache':False}}]}
 st['cloud_collect']={'cmd':rel+'.venv/bin/python collect.py','deps':['collect.py','cloud.py','results/execution.json'],'outs':['data/collected'],'metrics':[{'results/cleanup.json':{'cache':False}},{'results/permission-removed.json':{'cache':False}}]}
 if (p/'results/report.json').exists() and 'analyze_pilot' not in st:
  st['analyze']={'cmd':rel+'.venv/bin/python analyze_pilot.py','deps':['analyze_pilot.py','data/collected','results/report.json'],'outs':[{'results/summary.json':{'cache':False}}]}
 y.write_text(yaml.safe_dump(doc,sort_keys=False))
 for n in ['cloud_submit','cloud_collect']:
  subprocess.run([str(D),'commit','-f','dvc.yaml:'+n],cwd=p,check=True)
 if (p/'data/resume').exists():
  mapping={}
  for f in (p/'data/resume').glob('*.pt'):
   import hashlib
   h=hashlib.sha256(f.read_bytes()).hexdigest()
   candidates=list((e/'data/collected').glob('*.pt'))+list((e/'attempt02/data/collected').glob('*.pt'))+list((e/'attempt03/data/collected').glob('*.pt'))
   source=next(c for c in candidates if hashlib.sha256(c.read_bytes()).hexdigest()==h)
   import os
   mapping[f.name]=os.path.relpath(source,p)
  script='import shutil,json\nfrom pathlib import Path\nr=Path(__file__).parent\n(r/"data/resume").mkdir(parents=True,exist_ok=True)\nfor n,p in '+repr(mapping)+'.items():shutil.copy2(r/p,r/"data/resume"/n)\n'
  (p/'restore_inputs.py').write_text(script)
  doc['stages']['resume_inputs']={'cmd':rel+'.venv/bin/python restore_inputs.py','deps':['restore_inputs.py']+list(mapping.values()),'outs':['data/resume']};y.write_text(yaml.safe_dump(doc,sort_keys=False))
  subprocess.run([str(D),'commit','-f','dvc.yaml:resume_inputs'],cwd=p,check=True)
# Trained exp32 weights were extracted from the already archived cloud output tar.
p=R/'experiments/32_tree_expansion';y=p/'dvc.yaml';doc=yaml.safe_load(y.read_text());doc['stages']['extract_trained_models']={'cmd':'../../.venv/bin/python extract_trained_models.py','deps':['extract_trained_models.py','data/gpu/cloud/outputs.tar'],'outs':['data/models/geometry_snapshot.pt','data/models/hybrid.pt']};y.write_text(yaml.safe_dump(doc,sort_keys=False))
(p/'extract_trained_models.py').write_text("import tarfile\nfrom pathlib import Path\nr=Path(__file__).parent\nwith tarfile.open(r/'data/gpu/cloud/outputs.tar') as t:\n for n in ['data/models/geometry_snapshot.pt','data/models/hybrid.pt']:\n  m=t.getmember(n);assert m.isfile();(r/n).write_bytes(t.extractfile(m).read())\n")
subprocess.run([str(D),'commit','-f','dvc.yaml:extract_trained_models'],cwd=p,check=True)
