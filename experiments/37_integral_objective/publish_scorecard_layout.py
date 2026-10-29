from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;D=R/'data/scorecard-layout';proof=json.loads((R/'results/scorecard-layout.json').read_text());assert proof['passed']
api=HfApi();repo='wdavies/fire-reports';rev=proof['parent'];assert api.repo_info(repo,repo_type='space').sha==rev
assert Path(hf_hub_download(repo,'full-sequence/index.html',repo_type='space',revision=rev)).read_bytes()==(D/'before.html').read_bytes()
assert hashlib.sha256((D/'index.html').read_bytes()).hexdigest()==proof['sha256']
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo='full-sequence/index.html',path_or_fileobj=str(D/'index.html'))],commit_message='Separate integral-objective rotations into top summary table')
assert Path(hf_hub_download(repo,'full-sequence/index.html',repo_type='space',revision=c.oid)).read_bytes()==(D/'index.html').read_bytes()
(R/'results/scorecard-layout-publication.json').write_text(json.dumps(dict(commit=c.oid,parent=rev,readback_exact=True,only_path='full-sequence/index.html'),indent=2)+'\n');print(c.oid)
