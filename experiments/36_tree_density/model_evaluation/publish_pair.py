"""Publish only the requested derived pair gallery, scorecard and index."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/pair-sequence-r0-collected.json').read_text())['passed']
 api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
 existing=api.list_repo_files(repo,repo_type='space',revision=rev)
 assert not any(n.startswith('stride-one-pair/') for n in existing),'Reconcile previous publication before retry'
 score=R.parent/'35_surrogate_diagnostics/simple_scorecard/data'
 files={f'stride-one-pair/gallery/{p.name}':p for p in (R/'data/pair-gallery').iterdir() if p.is_file()}
 assert len(files)==72
 files.update({f'scorecard/{n}':score/'scorecard'/n for n in ('index.html','values.json','sources.json')});files['index.html']=score/'index.html'
 assert sum(p.stat().st_size for p in files.values())<30_000_000
 c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],commit_message='Add matched stride-one plain/gated results and shared-test gallery')
 for n in ['index.html','scorecard/index.html','scorecard/values.json','stride-one-pair/gallery/index.html','stride-one-pair/gallery/page-69.js']:
  assert Path(hf_hub_download(repo,filename=n,repo_type='space',revision=c.oid)).read_bytes()==files[n].read_bytes()
 proof=dict(repo=repo,commit=c.oid,parent_commit=rev,paths={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()},other_paths_unchanged=True,raw_data_published=False)
 (R/'results/pair-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(c.oid)
if __name__=='__main__':main()
