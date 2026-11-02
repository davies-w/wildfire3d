"""Adopt completed training-extraction stages and push directly to HF, no cache."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
import yaml
R=Path(__file__).resolve().parent;repo=R.parents[1]
def md5(p):
    h=hashlib.md5()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def record(path):
    p=R/path
    if p.is_file():return dict(path=path,hash='md5',md5=md5(p),size=p.stat().st_size)
    assert p.is_dir(),p
    files=sorted(x for x in p.rglob('*') if x.is_file())
    entries=[dict(md5=md5(x),relpath=x.relative_to(p).as_posix()) for x in files]
    value=hashlib.md5(json.dumps(entries,sort_keys=True).encode()).hexdigest()+'.dir'
    return dict(path=path,hash='md5',md5=value,size=sum(x.stat().st_size for x in files),nfiles=len(files))
def main():
    all_stages=['prepare_training','extract_training','summarize_training','report_training']
    stages=sys.argv[1:] or all_stages
    assert stages and all(s in all_stages for s in stages)
    proof=json.loads((R/'data/training-summary/validation.json').read_text())
    assert proof['passed'] and proof['training_histories']==1662 and proof['frames']==151242
    pipeline=yaml.safe_load((R/'dvc.yaml').read_text())
    receipt=R/'training-preservation.json';receipts=json.loads(receipt.read_text()) if receipt.exists() else {}
    env=dict(os.environ,HF_HUB_DISABLE_PROGRESS_BARS='1')
    for stage in stages:
        subprocess.run([sys.executable,'scripts/dvc_hf.py','commit',f'experiments/44_hot_gas_cones/dvc.yaml:{stage}'],cwd=repo,check=True,env=env)
        subprocess.run([sys.executable,'scripts/dvc_hf.py','push'],cwd=repo,check=True,env=env)
        result=json.loads((repo/'experiments/43_repository_preservation/results/direct-hf/upload-verification.json').read_text())
        assert result['passed'];receipts[stage]=result;receipt.write_text(json.dumps(receipts,indent=2)+'\n')
        print('Verified public HF:',stage,flush=True)
    # Hash dependency bytes as well as outputs; do not execute simulation stages.
    lock=yaml.safe_load((R/'dvc.lock').read_text());memo={}
    for stage in stages:
        deps=[]
        for path in pipeline['stages'][stage].get('deps',[]):
            if path not in memo:memo[path]=record(path)
            deps.append(memo[path])
        lock['stages'][stage]['deps']=deps
        lock['stages'][stage]['cmd']=pipeline['stages'][stage]['cmd']
    (R/'dvc.lock').write_text(yaml.safe_dump(lock,sort_keys=False))
    print('Requested training stages and dependency hashes recorded',flush=True)
if __name__=='__main__':main()
