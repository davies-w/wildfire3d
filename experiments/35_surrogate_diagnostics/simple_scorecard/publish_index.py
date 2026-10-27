"""Publish the report index only, using consistent cards for every report link."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parent;p=R/'data/index.html';api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=str(p))],commit_message='Use matching cards for denser report and gallery on report index')
assert Path(hf_hub_download(repo,filename='index.html',repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
(R/'index-publication.json').write_text(json.dumps({'commit':c.oid,'path':'index.html','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'url':'https://wdavies-fire-reports.static.hf.space/','other_paths_unchanged':True},indent=2)+'\n')
