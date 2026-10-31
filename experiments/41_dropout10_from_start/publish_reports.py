"""Publish only additive scientific reports; pinned parent and exact readback."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;D=R/'data/report-public';O=R/'results';proof=O/'report-publication.json';assert not proof.exists(),'Already published; inspect before any retry'
p=json.loads((O/'report-build.json').read_text());assert p['passed'];api=HfApi();repo='wdavies/fire-reports';rev=p['parent_revision'];assert api.repo_info(repo,repo_type='space').sha==rev
for n in ['index.html','full-sequence/index.html','full-sequence/gallery.html']:assert Path(hf_hub_download(repo,n,repo_type='space',revision=rev)).read_bytes()==(D/('parent-'+n.replace('/','__'))).read_bytes()
files={str(f.relative_to(D)):f for f in D.rglob('*') if f.is_file() and not f.name.startswith('parent-')};assert len(files)==7
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(f)) for n,f in files.items()],commit_message='Add fresh dropout-from-start report, matched scorecard and gallery')
for n,f in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==f.read_bytes()
proof.write_text(json.dumps(dict(commit=c.oid,readback_exact=True,files={n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in files.items()}),indent=2)+'\n');print(c.oid)
