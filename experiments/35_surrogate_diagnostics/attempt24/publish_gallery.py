"""Publish only the user-approved gallery assets to a public static HF Space."""
from pathlib import Path
import hashlib, json
from huggingface_hub import HfApi, CommitOperationAdd
R=Path(__file__).resolve().parent
D=R/'data/scenario_gallery'
repo='wdavies/fire-prediction-gallery'
readme='''---
title: Fire Prediction Gallery
emoji: 🌲
colorFrom: yellow
colorTo: green
sdk: static
app_file: index.html
pinned: false
---
# Fire Prediction Gallery
520 histories pooled across ten held-out test folds, comparing simulation, no-change, extrapolated first predicted delta and recursive gated-GRU predictions. Four values: derived water, dry vegetation, vegetation fuel-gas release (not heat release), and surface-heating index (not stored energy). Horizon grows from 2 to 32 seconds, then rolls at 32 seconds. Formerly examined, reshuffled data is not a pristine test set.

The tree infographic uses categorical height and moisture area scales, not literal geometry or water mass fractions. Green indicates one of five initial moisture settings; yellow is the remainder. Darker shades indicate higher fuel loading. Predictions are not clipped: water increases and negative values are model errors, not evidence of replenishment.

Generic 3 m-wide conical vegetation crowns, heights 4/6/8/10 m above a 2 m base, with documented legacy geometries; 1600 weighted particles, 0.5 m mesh in a 24×16×16 m domain, 180 s histories, imposed 1500°C ignition source for 20 s. No trunks, buildings or embers. Derived water/fuel use an audited integration and 0.75 fuel-gas yield; char is treated as inert ash. No physical validation.

Source: https://github.com/davies-w/wildfire3d/tree/codex/ignition-surrogate-pilot/experiments/35_surrogate_diagnostics/attempt24
'''
files=[D/'report.html',*sorted(D.glob('page-*.js'))]
assert len(files)==175
ops=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=readme.encode())]
manifest=[]
for p in files:
 target='index.html' if p.name=='report.html' else p.name
 ops.append(CommitOperationAdd(path_in_repo=target,path_or_fileobj=str(p)))
 manifest.append(dict(path=target,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
api=HfApi()
api.create_repo(repo_id=repo,repo_type='space',space_sdk='static',private=False,exist_ok=True)
commit=api.create_commit(repo_id=repo,repo_type='space',operations=ops,commit_message='Publish approved held-out fire prediction gallery')
proof=dict(repo=repo,url='https://huggingface.co/spaces/'+repo,commit=commit.oid,files=manifest)
(R/'results/gallery-publication.json').write_text(json.dumps(proof,indent=2))
print(proof['url']);print(commit.oid)
