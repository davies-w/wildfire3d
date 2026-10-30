"""Publish only the requested public document, learning curve and additive card."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;D=R/'data/document-index';api=HfApi();repo='wdavies/fire-reports';proof=R/'results08/document-publication.json'
assert not proof.exists(),'Already published; do not duplicate'
rev=json.loads((D/'parent.json').read_text())['revision'];assert api.repo_info(repo,repo_type='space').sha==rev
assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_bytes()==(D/'parent-index.html').read_bytes()
files={'index.html':D/'index.html','history38/index.html':R/'data/document/index.html','history38/learning-curve.png':R/'data/document/learning-curve.png'}
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],commit_message='Add experiment38 completion document and index card')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
proof.write_text(json.dumps({'commit':c.oid,'readback_exact':True,'files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}},indent=2));print(c.oid)
