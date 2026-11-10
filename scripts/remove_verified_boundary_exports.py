"""Remove only user-authorized historical ig_*.txt originals after preservation checks."""
from pathlib import Path
import hashlib,json,subprocess,fcntl
import yaml,requests
from huggingface_hub import HfApi
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 state=ROOT/'experiments/51_three_tree_campaign/private07/historical-boundary-text-preservation'
 with (state/'cleanup.lock').open('w') as guard:
  fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
  proof=json.loads((state/'complete.json').read_text());assert proof['passed'] and proof['restoration_sha256_verified']
  mapping=json.loads((state/'source-map.json').read_text());assert len(mapping)==1788
  folder=ROOT/'experiments/43_repository_preservation/data/reviewed-historical-boundary-text';pointer=folder.with_name(folder.name+'.dvc');md=yaml.safe_load(pointer.read_text())['outs'][0]['md5']
  committed=subprocess.check_output(['git','show',proof['git_commit']+':'+str(pointer.relative_to(ROOT))],cwd=ROOT);assert committed==pointer.read_bytes()
  subprocess.run(['git','fetch','origin'],cwd=ROOT,check=True)
  subprocess.run(['git','merge-base','--is-ancestor',proof['git_commit'],'@{u}'],cwd=ROOT,check=True)
  response=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+md[:2]+'/'+md[2:],timeout=90);response.raise_for_status();assert hashlib.md5(response.content).hexdigest()==md[:-4]
  entries={x['relpath']:x['md5'] for x in response.json()};api=HfApi();paths={'wildfire3d/files/md5/'+v[:2]+'/'+v[2:] for v in entries.values()};found=set()
  for start in range(0,len(paths),1000):found.update(x.path for x in api.get_bucket_paths_info('wdavies/dvc_storage',sorted(paths)[start:start+1000]))
  assert found==paths
  targets=[]
  for row in mapping:
   p=ROOT/row['original_path'];assert p.name.startswith('ig_') and p.suffix=='.txt' and p.resolve().is_relative_to(ROOT) and not p.is_symlink()
   archived=folder/row['archived_filename'];restored=ROOT/'.artifact-staging/reviewed-historical-boundary-text-roundtrip'/archived.relative_to(ROOT)
   assert sha(archived)==row['sha256'] and sha(restored)==row['sha256']
   with archived.open('rb') as f:assert hashlib.file_digest(f,'md5').hexdigest()==entries[row['archived_filename']]
   assert p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'];targets.append((p,row))
  receipt={'authorization':'User explicitly requested deletion of these backed-up boundary text originals','dvc_md5':md,'git_commit':proof['git_commit'],'remote_manifest_md5_verified':True,'all_remote_member_paths_present':True,'restored_sha256_reverified':True,'removed':[]}
  for p,row in targets:
   assert not p.is_symlink() and sha(p)==row['sha256'];p.unlink();receipt['removed'].append(row)
   (state/'local-original-deletion.json').write_text(json.dumps(receipt,indent=2)+'\n')
  receipt['passed']=True;receipt['bytes_removed']=sum(x['bytes'] for x in receipt['removed']);(state/'local-original-deletion.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Removed',len(targets),'original files;',receipt['bytes_removed'],'bytes. Archive and restoration copies retained.')
if __name__=='__main__':main()
