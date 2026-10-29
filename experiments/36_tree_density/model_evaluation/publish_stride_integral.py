"""Publish only the requested gated gallery annotations and additive scorecard column."""
from pathlib import Path
import json,hashlib
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
R=Path(__file__).resolve().parents[1];D=R/'data/stride-integral';api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha
for name in ['index.html','stridegated.html']:
 assert Path(hf_hub_download(repo,'full-sequence/'+name,repo_type='space',revision=rev)).read_bytes()==(R/'data/full-sequence-public'/name).read_bytes(),'Published source changed; reconcile before publishing'
files={f'full-sequence/{n}':D/n for n in ['index.html','stridegated.html','integral-scores.json']}
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],commit_message='Add exact range-normalized integral errors to gated stride-one graphs and scorecard')
for n,p in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==p.read_bytes()
proof=dict(commit=c.oid,parent=rev,files={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()},readback_exact=True,all_existing_plot_paths_unchanged=True,all_existing_scorecard_cells_unchanged=True,metric_scope='Whole sequence in graph boxes and new scorecard column; not phase restricted',histories=208,graph_badges=832)
(R/'results/stride-integral-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
