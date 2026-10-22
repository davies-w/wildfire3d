"""Preserve cached objects referenced by retired lock stages without recreating simulations."""
import json,hashlib,shutil
from pathlib import Path
import yaml
R=Path(__file__).resolve().parents[1];rows=[]
for name,stages in [('03_vegetation',['solve_veg','solve_veg_obst']),('08_isolated_ember_ignition',['solve_ember']),('23_mesh_domain_pilot',['prepare'])]:
 d=yaml.safe_load((R/'experiments'/name/'dvc.lock').read_text())
 for s in stages:
  for o in d['stages'][s]['outs']:
   h=o['md5'];rel=Path('files/md5')/h[:2]/h[2:];src=R/'.dvc/cache'/rel;dst=R/'FDS/hf_dvc_mirror'/rel
   if not src.exists(): rows.append(dict(stage=s,md5=h,status='missing_local_cache'));continue
   assert hashlib.md5(src.read_bytes()).hexdigest()==h
   if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
   assert hashlib.md5(dst.read_bytes()).hexdigest()==h
   rows.append(dict(stage=s,md5=h,status='verified_in_mirror'))
(R/'docs/retired-stage-archive.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'objects;',sum(x['status']!='verified_in_mirror' for x in rows),'missing')
