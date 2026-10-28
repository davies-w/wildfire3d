"""Publish only new full-sequence paths and append cards without modifying old cards."""
from pathlib import Path
import json,hashlib,re
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parents[1];D=R/'data/full-sequence-public';api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
assert json.loads((D/'scores.json').read_text())['chart_metric_readback_passed']
names=api.list_repo_files(repo,repo_type='space',revision=rev);assert not any(n.startswith('full-sequence/') for n in names),'Already published: inspect before retry'
old=Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_text()
cards=''.join('<a class="card" href="'+p+'" target="_blank" rel="noopener noreferrer"><span class="tag">Full sequence · no truth resets</span><h2>'+title+' →</h2><p>'+desc+'</p></a>' for p,title,desc in [('full-sequence/index.html','Full-sequence scorecard','Seven archived model variants. Scores from continuous 90-step rollouts initialized once, with original scores preserved separately.'),('full-sequence/gallery.html','Full-sequence visual comparisons','The same continuous trajectories used by the new scorecard. Simulation, model prediction and hold-initial-state reference.')])
marker='<div class="cards">';assert old.count(marker)==1;new=old.replace(marker,marker+cards,1);assert new.replace(cards,'',1)==old
allowed={'index.html','gallery.html','mlp3.html','gru3.html','plain4.html','gated4.html','dense.html','strideplain.html','stridegated.html','scores.json','historical-scores.json'};assert {p.name for p in D.iterdir()}==allowed;files={f'full-sequence/{n}':D/n for n in sorted(allowed)};ops=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()];ops.append(CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=new.encode()))
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=ops,commit_message='Add full-sequence scorecard and matching autonomous trajectory gallery; preserve existing cards')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=c.oid)).read_text()==new
proof=dict(commit=c.oid,parent=rev,existing_cards_unchanged=True,existing_report_paths_unchanged=True,all_new_assets_readback_exact=True,files={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()})
(R/'results/full-sequence-publication.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
