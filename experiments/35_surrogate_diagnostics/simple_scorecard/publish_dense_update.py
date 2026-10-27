"""Update only the requested existing simple scorecard; leave galleries/hub untouched."""
from pathlib import Path
import hashlib,json
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parent
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
files=[R/'data/scorecard'/n for n in ['index.html','values.json','sources.json']]
commit=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo='scorecard/'+p.name,path_or_fileobj=str(p)) for p in files],commit_message='Add plain four-state dense GRU results to Simple Scorecard')
for p in files:
 remote=Path(hf_hub_download(repo,filename='scorecard/'+p.name,repo_type='space',revision=commit.oid));assert remote.read_bytes()==p.read_bytes()
proof={'commit':commit.oid,'url':'https://wdavies-fire-reports.static.hf.space/scorecard/index.html','paths':['scorecard/'+p.name for p in files],'dense_source_sha256':hashlib.sha256((R/'../../36_tree_density/results/model-four-state-summary.json').read_bytes()).hexdigest(),'label':'4-state plain GRU · dense','other_published_paths_unchanged':True}
(R/'dense-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof['url'])
