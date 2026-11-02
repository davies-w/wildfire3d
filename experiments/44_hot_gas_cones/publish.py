"""Add a scoped report to the existing storyboard Space; preserve earlier pages."""
from pathlib import Path
import json,hashlib,requests
from huggingface_hub import HfApi,CommitOperationAdd,get_token
R=Path(__file__).resolve().parent;repo='wdavies/fire-state-storyboards';api=HfApi()
response=requests.get(f'https://huggingface.co/spaces/{repo}/resolve/main/index.html',headers={'Authorization':'Bearer '+get_token()},timeout=60);response.raise_for_status();old=response.text
link='<section><h2>Five-parameter cone comparison</h2><p><a href="cones44/index.html">Inspect cone fits, original ovoids and measured hot-gas coverage across48 histories.</a> These are source envelopes, not ignition boundaries.</p></section>'
updated=old if 'cones44/index.html' in old else (old.replace('</body>',link+'</body>') if '</body>' in old else old+'\n'+link)
ops=[CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=updated.encode())];files=[]
for p in sorted((R/'data').rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(R/'data').as_posix();dest='cones44/'+('index.html' if rel=='report.html' else rel)
 ops.append(CommitOperationAdd(path_in_repo=dest,path_or_fileobj=str(p)))
 files.append(dict(path=dest,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
commit=api.create_commit(repo_id=repo,repo_type='space',operations=ops,commit_message='Add five-parameter hot-gas cone fit and ovoid comparison')
receipt=dict(repo=repo,commit=commit.oid,url='https://wdavies-fire-state-storyboards.static.hf.space/cones44/index.html',files=files,previous_index_sha256=hashlib.sha256(old.encode()).hexdigest(),earlier_pages_preserved=True)
(R/'publication.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['url'],commit.oid)
