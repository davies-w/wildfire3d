"""Check exact historical DVC hashes remotely; retain downloaded evidence privately."""
import json,hashlib
from pathlib import Path
from huggingface_hub import HfApi
ROOT=Path(__file__).resolve().parents[1]
def main():
 state=ROOT/'experiments/51_three_tree_campaign/private07/missing-output-remote';state.mkdir(exist_ok=True)
 rows=json.loads((state.parent/'missing-output-reconciliation.json').read_text())['unresolved'];api=HfApi();result=[]
 for row in rows:
  md=row['md5'];objpath='wildfire3d/files/md5/'+md[:2]+'/'+md[2:];remote=list(api.get_bucket_paths_info('wdavies/dvc_storage',[objpath]));r={'path':row['path'],'md5':md,'remote_present':bool(remote)}
  if remote:
   dest=state/md
   api.download_bucket_files('wdavies/dvc_storage',[(remote[0],dest)],raise_on_missing_files=True)
   assert hashlib.md5(dest.read_bytes()).hexdigest()==md.removesuffix('.dir');r['download_md5_verified']=True
   if md.endswith('.dir'):
    entries=json.loads(dest.read_text());paths={'wildfire3d/files/md5/'+x['md5'][:2]+'/'+x['md5'][2:] for x in entries};found=set()
    for start in range(0,len(paths),1000):found.update(x.path for x in api.get_bucket_paths_info('wdavies/dvc_storage',sorted(paths)[start:start+1000]))
    r.update(manifest_files=len(entries),unique_objects=len(paths),missing_remote_objects=sorted(paths-found),all_member_paths_present=paths==found)
  result.append(r);(state/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(md,r['remote_present'],r.get('all_member_paths_present','file'),flush=True)
if __name__=='__main__':main()
