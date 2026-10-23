"""Publish only the prepared public report assets to free static hosting."""
from pathlib import Path
import hashlib,json
from huggingface_hub import HfApi,CommitOperationAdd
R=Path(__file__).resolve().parent
repo='wdavies/fire-state-storyboards'
files=[R/'data/report.html',*sorted((R/'data/storyboards').glob('*.png')),*sorted((R/'data/states').glob('*.json'))]
assert len(list((R/'data/storyboards').glob('*.png')))==48
readme='''---
title: Fire State Storyboards
emoji: 🌲
colorFrom: yellow
colorTo: gray
sdk: static
app_file: index.html
pinned: false
---
# Fire State Storyboards
48 simulated fire histories with twelve storyboard panels through 90 seconds and full numeric histories through 180 seconds. Measured FDS outputs and derived summaries, not learned predictions or physical validation.

Generic 3 m-wide conical crowns above 2 m, 0.5 m grid, artificial 1500°C ignition source for 20 seconds; no trunks, buildings or embers. Orange arrows summarize hot-gas position, not energy transport. Detailed definitions and limitations are in the report.

Source and reproduction: https://github.com/davies-w/wildfire3d/tree/codex/ignition-surrogate-pilot/experiments/35_surrogate_diagnostics/attempt11
'''
ops=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=readme.encode())]
manifest=[]
for p in files:
 target='index.html' if p.name=='report.html' else p.relative_to(R/'data').as_posix()
 ops.append(CommitOperationAdd(path_in_repo=target,path_or_fileobj=str(p)))
 manifest.append(dict(path=target,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
api=HfApi();api.create_repo(repo_id=repo,repo_type='space',space_sdk='static',private=False,exist_ok=True)
commit=api.create_commit(repo_id=repo,repo_type='space',operations=ops,commit_message='Publish all 48 fire state storyboards and numeric histories')
proof=dict(repo=repo,url='https://huggingface.co/spaces/'+repo,app_url='https://wdavies-fire-state-storyboards.static.hf.space',commit=commit.oid,files=manifest)
(R/'results/space-publication.json').write_text(json.dumps(proof,indent=2))
print(proof['url']);print('Commit:',commit.oid)
