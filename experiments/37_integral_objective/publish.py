"""Publish only new derived report pages and append matching index cards."""
from pathlib import Path
import json,hashlib,re
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parent;D=R/'data/public';api=HfApi();repo='wdavies/fire-reports'
assert json.loads((R/'results/training03-collected.json').read_text())['passed'];assert json.loads((R/'results/public-build.json').read_text())['passed']
assert not (R/'results/publication.json').exists(),'Publication exists; reconcile rather than repeat'
rev=json.loads((R/'results/public-parent.json').read_text())['revision'];assert api.repo_info(repo,repo_type='space').sha==rev,'Remote changed; reconcile before publishing'
old=(D/'main-index-original.html').read_text();assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_text()==old
assert not any(p.startswith('integral37/') for p in api.list_repo_files(repo,repo_type='space',revision=rev))
cards=''.join('<a class="card" href="'+path+'" target="_blank" rel="noopener noreferrer"><span class="tag">Integral objective · same held-out split</span><h2>'+title+' →</h2><p>'+desc+'</p></a>' for path,title,desc in [('integral37/index.html','Integral-objective scorecard','New gated-GRU objective compared with preserved prior scores. Same208 test histories; full-sequence integral percentages.'),('integral37/gated.html','Integral-objective visual comparisons','Three scenarios per page, four states per row, original line toggles and tree/wind/ignition rubric. Exact integral error boxes.')])
assert old.count('</div><div class="foot">')==1
new=old.replace('</div><div class="foot">',cards+'</div><div class="foot">',1);assert new.replace(cards,'')==old
(D/'main-index.html').write_text(new)
files={f'integral37/{n}':D/n for n in ['index.html','gated.html','integral-comparison.json']};files['index.html']=D/'main-index.html'
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],commit_message='Add integral-objective gated GRU report and gallery; preserve prior pages')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
proof=dict(commit=c.oid,parent=rev,files={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()},readback_exact=True,prior_pages_unchanged=True,existing_index_cards_unchanged=True,first_explanation_card_preserved=True)
(R/'results/publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
