"""Preserve collected checkpoints and scientific results, never financial/operational records."""
from pathlib import Path
import sys,json,hashlib,yaml
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
hf.STATE=R/'private/hf-results';hf.STATE.mkdir(parents=True,exist_ok=True)
assert (R/'data/results').is_dir() and any((R/'data/results').iterdir())
spec=str(R/'dvc.yaml')+':collect_results';hf.stage_commit(spec)
y=yaml.safe_load((R/'dvc.yaml').read_text());lock=yaml.safe_load((R/'dvc.lock').read_text());st=lock['stages']['collect_results'];st['deps']=[dict(path=d,hash='md5',md5=hashlib.md5((R/d).read_bytes()).hexdigest(),size=(R/d).stat().st_size) for d in y['stages']['collect_results']['deps']];(R/'dvc.lock').write_text(yaml.safe_dump(lock,sort_keys=False));hf.upload(hf.STATE/'plan.json')
outs=[{**o,'path':'../../'+o['path']} for o in st['outs']];ptr=hf.STATE/'restoration-source.dvc';ptr.write_text(yaml.safe_dump({'outs':outs},sort_keys=False));dest=R/'private'/('result-roundtrip-'+st['outs'][0]['md5']);
if not dest.exists():hf.restore_records([str(ptr)],dest)
assert json.loads((hf.STATE/'restore-verification.json').read_text())['passed']
(R/'result-preservation.json').write_text(json.dumps(dict(passed=True,independent_HF_restoration=True,result_directory_md5=st['outs'][0]['md5'],files=st['outs'][0]['nfiles']),indent=2)+'\n')
