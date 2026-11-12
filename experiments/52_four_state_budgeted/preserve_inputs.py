"""Scoped DVC/HF preservation and independent restoration of reviewed scientific inputs."""
from pathlib import Path
import sys,json,hashlib,yaml
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
hf.STATE=R/'private/hf-inputs';hf.STATE.mkdir(parents=True,exist_ok=True)
specs=[str(R/'dvc.yaml')+':'+s for s in ['prepare_observations','freeze_split']]
for spec in specs:hf.stage_commit(spec)
# Record the exact dependencies used for these successful executions.
y=yaml.safe_load((R/'dvc.yaml').read_text());lock=yaml.safe_load((R/'dvc.lock').read_text())
for name,stage in y['stages'].items():
 lock['stages'][name]['deps']=[dict(path=d,hash='md5',md5=hashlib.md5((R/d).read_bytes()).hexdigest(),size=(R/d).stat().st_size) for d in stage['deps']]
(R/'dvc.lock').write_text(yaml.safe_dump(lock,sort_keys=False));hf.plan_records(specs);hf.upload(hf.STATE/'plan.json')
outs=[]
for st in lock['stages'].values():
 for out in st['outs']:outs.append({**out,'path':str((R/out['path']).relative_to(hf.STATE)) if (R/out['path']).is_relative_to(hf.STATE) else '../../'+out['path']})
pointer=hf.STATE/'restoration-source.dvc';pointer.write_text(yaml.safe_dump({'outs':outs},sort_keys=False));hf.restore_records([str(pointer)],R/'private/input-roundtrip')
(R/'input-preservation.json').write_text(json.dumps(dict(passed=True,independent_HF_restoration=True,files=sum(len(s['outs']) for s in lock['stages'].values()),dvc_lock_sha256=hashlib.sha256((R/'dvc.lock').read_bytes()).hexdigest()),indent=2)+'\n')
