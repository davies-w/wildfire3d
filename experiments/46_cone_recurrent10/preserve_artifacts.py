"""Direct reviewed DVC/HF push; cache-free dependency hashes and stage receipt."""
from pathlib import Path
import sys,json,yaml,subprocess,os
R=Path(__file__).resolve().parent;repo=R.parents[1];sys.path.insert(0,str(R.parent/'44_hot_gas_cones'))
from preserve_training import md5
import hashlib
def record(path):
 p=R/path
 if p.is_file():return dict(path=path,hash='md5',md5=md5(p),size=p.stat().st_size)
 assert p.is_dir(),p
 fs=sorted(x for x in p.rglob('*') if x.is_file());entries=[dict(md5=md5(x),relpath=x.relative_to(p).as_posix()) for x in fs]
 return dict(path=path,hash='md5',md5=hashlib.md5(json.dumps(entries,sort_keys=True).encode()).hexdigest()+'.dir',size=sum(x.stat().st_size for x in fs),nfiles=len(fs))
def main():
 stage=sys.argv[1];assert stage in ['prepare','progress','collect','interrupted','prepare02','prepare03','report'];env=dict(os.environ,HF_HUB_DISABLE_PROGRESS_BARS='1')
 subprocess.run([sys.executable,'scripts/dvc_hf.py','commit',f'experiments/46_cone_recurrent10/dvc.yaml:{stage}'],cwd=repo,check=True,env=env)
 subprocess.run([sys.executable,'scripts/dvc_hf.py','push'],cwd=repo,check=True,env=env)
 proof=json.loads((repo/'experiments/43_repository_preservation/results/direct-hf/upload-verification.json').read_text());assert proof['passed']
 (R/f'public-{stage}-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
 lock=yaml.safe_load((R/'dvc.lock').read_text());pipeline=yaml.safe_load((R/'dvc.yaml').read_text());lock['stages'][stage]['deps']=[record(p) for p in pipeline['stages'][stage].get('deps',[])];(R/'dvc.lock').write_text(yaml.safe_dump(lock,sort_keys=False));print('Preserved',stage,flush=True)
if __name__=='__main__':main()
