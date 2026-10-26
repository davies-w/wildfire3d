"""Publish only the explicitly requested public report hub and rendered reports."""
from pathlib import Path
import hashlib,json
from huggingface_hub import HfApi,CommitOperationAdd
R=Path(__file__).resolve().parent
repo='wdavies/fire-reports'
files=sorted(p for p in (R/'data').rglob('*') if p.is_file())
assert len(files)<30 and sum(p.stat().st_size for p in files)<2_000_000
readme='''---
title: Fire Prediction Reports
emoji: 🌲
colorFrom: blue
colorTo: green
sdk: static
app_file: index.html
pinned: false
---
# Fire prediction reports
Index of the fire prediction scorecard, scenario gallery, simulation storyboards and training-data learning curve.

The simplified scorecard compares three-state MLP, plain four-state GRU and gated four-state GRU predictions 16 seconds ahead, using frozen active and quiet definitions over ten test folds. Models span experiments; this is not a controlled architecture-only comparison. No four-state MLP was trained.

Heating is a surface-heating index, not stored energy; gas means vegetation fuel-gas release, not combustion heat. Generic 3 m-wide conical crowns, heights 4/6/8/10 m above a 2 m base, 1600 weighted particles, .5 m grid in a 24×16×16 m domain, artificial 1500°C ignition for20s, 180s histories. 48legacy geometries retained. No trunks, buildings, embers or physical validation. Previously examined, reshuffled tests are not pristine.

Source: https://github.com/davies-w/wildfire3d/tree/codex/ignition-surrogate-pilot/experiments/35_surrogate_diagnostics/simple_scorecard
'''
api=HfApi();api.create_repo(repo_id=repo,repo_type='space',space_sdk='static',private=False,exist_ok=True)
ops=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=readme.encode())]
manifest=[]
for p in files:
 rel=p.relative_to(R/'data').as_posix()
 ops.append(CommitOperationAdd(path_in_repo=rel,path_or_fileobj=str(p)))
 manifest.append({'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
c=api.create_commit(repo_id=repo,repo_type='space',operations=ops,commit_message='Publish requested fire report index and simplified active/quiet scorecard')
proof={'repo':repo,'url':'https://huggingface.co/spaces/'+repo,'commit':c.oid,'files':manifest}
(R/'publication.json').write_text(json.dumps(proof,indent=2))
print(proof['url']);print(c.oid)
