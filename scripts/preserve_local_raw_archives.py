"""Preserve reviewed historical split archives; retain all originals and restores."""
from pathlib import Path
import argparse, fcntl, hashlib, json, subprocess
import dvc_hf as hf
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--queue',type=Path,required=True);ap.add_argument('--review',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--receipts',type=Path,required=True);a=ap.parse_args()
 output=a.output.resolve();state=a.receipts.resolve();assert output.is_relative_to(ROOT) and state.is_relative_to(ROOT)
 output.mkdir(parents=True,exist_ok=True);state.mkdir(parents=True,exist_ok=True)
 review={v['manifest']:v for v in json.loads(a.review.read_text())['archives']}
 with (state/'worker.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for row in json.loads(a.queue.read_text())['archives']:
   assert row['passed'];policy=review[row['manifest']];assert policy['public_policy_passed'] and not policy['exclusion_reason'];key=policy['archive_sha256'];work=state/key;work.mkdir(exist_ok=True);receipt=work/'complete.json'
   if receipt.exists():assert json.loads(receipt.read_text())['passed'];continue
   archive=output/(key+'.tar.gz');manifest=json.loads(Path(row['manifest']).read_text());assert manifest['complete'] and len(manifest['parts'])==len(row['parts'])
   # Revalidate every source part; never mutate a checkpoint or source manifest.
   for part,record in zip(manifest['parts'],row['parts']):
    p=Path(record['path']);assert p==Path(row['manifest']).parent/part['name'] and p.is_relative_to(ROOT) and not p.is_symlink();assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256']==record['sha256']
   if not archive.exists():
    temporary=archive.with_suffix('.partial')
    with temporary.open('wb') as target:
     for part in row['parts']:
      with Path(part['path']).open('rb') as source:
       while chunk:=source.read(8*1024*1024):target.write(chunk)
    assert temporary.stat().st_size==policy['bytes'] and sha(temporary)==key;temporary.replace(archive)
   assert archive.stat().st_size==policy['bytes'] and sha(archive)==key
   hf.STATE=work/'hf';hf.STATE.mkdir(exist_ok=True);hf.objects.clear();hf._hashes.clear();hf.review.clear();pointer=archive.with_name(archive.name+'.dvc')
   if pointer.exists():hf.plan_records([str(pointer)])
   else:hf.track([str(archive)])
   plan=hf.STATE/'plan.json';assert len(json.loads(plan.read_text())['objects'])==1;hf.upload(plan)
   dest=ROOT/'.artifact-staging/local-archive-roundtrip'/key
   if not (hf.STATE/'restore-verification.json').exists():hf.restore_records([str(pointer)],dest)
   assert json.loads((hf.STATE/'restore-verification.json').read_text())['passed'];assert sha(dest/archive.relative_to(ROOT))==key
   with (ROOT/'.git/preservation-publish.lock').open('w') as publish:
    fcntl.flock(publish,fcntl.LOCK_EX);paths=[str(pointer.relative_to(ROOT)),str((output/'.gitignore').relative_to(ROOT))];subprocess.run(['git','add','-f','--',*paths],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet','--',*paths],cwd=ROOT).returncode:subprocess.run(['git','commit','--only','-m','Preserve reviewed local raw archive with verified HF restoration','--',*paths],cwd=ROOT,check=True)
    subprocess.run(['git','push'],cwd=ROOT,check=True);head=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/'+git('branch','--show-current')).split()[0];assert remote==head
   save(receipt,{'passed':True,'source_manifest':row['manifest'],'archive_sha256':key,'bytes':policy['bytes'],'remote_hashes_verified':True,'restoration_sha256_verified':True,'git_commit':head,'original_parts_retained':True,'restore_retained':True});print('LOCAL ARCHIVE PRESERVED',key,flush=True)
if __name__=='__main__':main()
