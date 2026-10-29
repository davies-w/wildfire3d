"""Guarded publication of additive full-sequence results only."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;D=R/'data/scorecard-addition';api=HfApi();repo='wdavies/fire-reports'
assert json.loads((R/'results/scorecard-addition-build.json').read_text())['passed']
proof=R/'results/scorecard-addition-publication.json';assert not proof.exists()
rev=json.loads((R/'results/scorecard-addition-parent.json').read_text())['revision'];assert api.repo_info(repo,repo_type='space').sha==rev
for n in ['index.html','gallery.html']:
 assert Path(hf_hub_download(repo,'full-sequence/'+n,repo_type='space',revision=rev)).read_bytes()==(D/('full-sequence__'+n)).read_bytes()
files={f'full-sequence/{n}':D/n for n in ['index.html','gallery.html','integral-gated.html']}
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],commit_message='Append integral-objective model to full-sequence scorecard and matching gallery')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
proof.write_text(json.dumps(dict(commit=c.oid,parent=rev,readback_exact=True,files={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}),indent=2)+'\n');print(c.oid)
