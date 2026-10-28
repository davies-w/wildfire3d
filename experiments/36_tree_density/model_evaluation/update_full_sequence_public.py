"""Update only the new full-sequence reports; preserve every prior report/card."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parents[1];D=R/'data/full-sequence-public'
api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
old=Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_text()
a='The same continuous trajectories used by the new scorecard. Simulation, model prediction and hold-initial-state reference.'
b='The same continuous trajectories used by the new scorecard. Simulation, model prediction and previous-simulation-state reference.'
assert old.count(a)==1
new=old.replace(a,b);assert new.replace(b,a)==old
allowed={'index.html','gallery.html','mlp3.html','gru3.html','plain4.html','gated4.html','dense.html','strideplain.html','stridegated.html','scores.json','historical-scores.json'}
assert {p.name for p in D.iterdir()}==allowed
assert json.loads((D/'scores.json').read_text())['chart_metric_readback_passed']
files={f'full-sequence/{n}':D/n for n in sorted(allowed)}
ops=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()]
ops.append(CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=new.encode()))
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=ops,commit_message='Match simplified layout and correct full-sequence no-change reference to previous actual simulation state')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=c.oid)).read_text()==new
proof=dict(commit=c.oid,parent=rev,original_cards_and_reports_unchanged=True,all_assets_readback_exact=True,files={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()})
(R/'results/full-sequence-baseline-update-publication.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
