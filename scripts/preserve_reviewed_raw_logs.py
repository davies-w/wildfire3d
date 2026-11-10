"""Preserve exact reviewed historical raw/log bytes, retaining original files."""
from pathlib import Path
import argparse, fcntl, hashlib, json, shutil, subprocess
import dvc_hf as hf
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--review',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--state',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();state=a.state.resolve();assert out.is_relative_to(ROOT) and state.is_relative_to(ROOT);out.mkdir(parents=True,exist_ok=True);state.mkdir(parents=True,exist_ok=True)
 with (state/'worker.lock').open('w') as guard:
  fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if (state/'complete.json').exists():assert json.loads((state/'complete.json').read_text())['passed'];return
  rows=json.loads(a.review.read_text())['files'];mapping=[]
  for row in rows:
   source=ROOT/row['path'];assert row['public_policy_passed'] and not row['exclusion_reason'];assert source.resolve().is_relative_to(ROOT) and not source.is_symlink();assert source.stat().st_size==row['bytes'] and sha(source)==row['sha256'];assert hf.approve(source) is None
   target=out/(row['sha256']+source.suffix)
   if target.exists():assert sha(target)==row['sha256']
   else:shutil.copyfile(source,target)
   assert sha(target)==row['sha256'];mapping.append({'original_path':row['path'],'archived_filename':target.name,'sha256':row['sha256'],'bytes':row['bytes']})
  # Original paths remain private bookkeeping; archive names are content hashes.
  (state/'source-map.json').write_text(json.dumps(mapping,indent=2)+'\n');hf.STATE=state/'hf';hf.STATE.mkdir(exist_ok=True);pointer=out.with_name(out.name+'.dvc')
  if pointer.exists():hf.plan_records([str(pointer)])
  else:hf.track([str(out)])
  hf.upload(hf.STATE/'plan.json');dest=ROOT/'.artifact-staging'/(out.name+'-roundtrip')
  if not (hf.STATE/'restore-verification.json').exists():hf.restore_records([str(pointer)],dest)
  assert json.loads((hf.STATE/'restore-verification.json').read_text())['passed']
  for row in mapping:assert sha(dest/out.relative_to(ROOT)/row['archived_filename'])==row['sha256'] and sha(ROOT/row['original_path'])==row['sha256']
  with (ROOT/'.git/preservation-publish.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);paths=[str(pointer.relative_to(ROOT)),str((out.parent/'.gitignore').relative_to(ROOT))];subprocess.run(['git','add','-f','--',*paths],cwd=ROOT,check=True)
   if subprocess.run(['git','diff','--cached','--quiet','--',*paths],cwd=ROOT).returncode:subprocess.run(['git','commit','--only','-m','Preserve reviewed raw inputs and logs with HF restoration','--',*paths],cwd=ROOT,check=True)
   subprocess.run(['git','push'],cwd=ROOT,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0];assert head==remote
  result={'passed':True,'original_files':len(mapping),'unique_archived_files':len({x['archived_filename'] for x in mapping}),'restoration_sha256_verified':True,'originals_retained':True,'git_commit':head};(state/'complete.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
