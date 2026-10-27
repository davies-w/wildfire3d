"""Publish new denser paths only; never modify existing report/gallery paths."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parents[1]
def main():
 api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
 existing=api.list_repo_files(repo,repo_type='space',revision=rev);assert not any(x.startswith('denser/') for x in existing),'Reconcile existing publication before retry'
 root=R/'data/denser';files=sorted(p for p in root.rglob('*') if p.is_file());assert len(files)==698 and sum(p.stat().st_size for p in files)<100_000_000
 manifest=[dict(path='denser/'+p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in files]
 c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=m['path'],path_or_fileobj=str(p)) for p,m in zip(files,manifest)],commit_message='Add separate denser simple scorecard and prediction gallery; preserve existing reports')
 for path in ['denser/index.html','denser/gallery/index.html','denser/gallery/page-693.js']:
  p=Path(hf_hub_download(repo,filename=path,repo_type='space',revision=c.oid));assert hashlib.sha256(p.read_bytes()).hexdigest()==next(m['sha256'] for m in manifest if m['path']==path)
 proof=dict(repo=repo,commit=c.oid,parent_commit=rev,only_added_prefix='denser/',existing_paths_untouched=True,files=manifest,scorecard_url='https://wdavies-fire-reports.static.hf.space/denser/index.html',gallery_url='https://wdavies-fire-reports.static.hf.space/denser/gallery/index.html')
 (R/'results/denser-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof['scorecard_url']);print(proof['gallery_url'])
if __name__=='__main__':main()
