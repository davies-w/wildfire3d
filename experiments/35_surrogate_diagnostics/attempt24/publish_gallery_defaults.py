"""Publish only both gallery entry pages after changing comparison-line defaults."""
from pathlib import Path
import hashlib,json
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
ROOT=Path(__file__).resolve().parents[3]
api=HfApi();proof=[]
for repo,target,local,url in [
 ('wdavies/fire-prediction-gallery','index.html','experiments/35_surrogate_diagnostics/attempt24/data/scenario_gallery/report.html','https://wdavies-fire-prediction-gallery.static.hf.space/'),
 ('wdavies/fire-reports','denser/gallery/index.html','experiments/36_tree_density/data/denser/gallery/index.html','https://wdavies-fire-reports.static.hf.space/denser/gallery/index.html')]:
 p=ROOT/local;s=p.read_text()
 assert 'visible=[true,false,false,true]' in s
 for k in [1,2]:assert f'data-series="{k}" aria-pressed="false"' in s
 rev=api.repo_info(repo,repo_type='space').sha
 c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=target,path_or_fileobj=str(p))],commit_message='Default No change and first predicted change lines to off')
 assert Path(hf_hub_download(repo,filename=target,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
 proof.append(dict(repo=repo,path=target,commit=c.oid,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),url=url))
 print(url,c.oid)
(Path(__file__).resolve().parent/'results/gallery-defaults-publication.json').write_text(json.dumps(proof,indent=2)+'\n')
