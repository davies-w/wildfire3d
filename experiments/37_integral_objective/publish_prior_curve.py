from pathlib import Path
import json
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;proof=R/'results/prior-overlay-publication.json';assert not proof.exists()
a=HfApi();repo='wdavies/fire-reports';rev=a.repo_info(repo,repo_type='space').sha;n='full-sequence/integral-gated.html'
assert Path(hf_hub_download(repo,n,repo_type='space',revision=rev)).read_bytes()==(R/'data/scorecard-addition/integral-gated.html').read_bytes()
p=R/'data/prior-overlay/integral-gated.html';c=a.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p))],commit_message='Overlay previous stride-one gated curve in integral gallery')
assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
proof.write_text(json.dumps(dict(commit=c.oid,parent=rev,path=n,readback_exact=True),indent=2)+'\n');print(c.oid)
