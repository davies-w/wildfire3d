"""Preserve excluded originals and audit evidence to the local mirror only."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;ROOT=R.parents[1];D=R/'data/private';D.mkdir(parents=True,exist_ok=True)
names=[]
for name in ['private-git-paths.json','additional-ledger-paths.json','untracked-metadata-inventory.json']:
 names+=json.loads((R/'results'/name).read_text())
for name in sorted(set(names)):
 p=ROOT/name
 if p.is_file():d=D/'originals'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
shutil.copytree(R/'results',D/'audit',dirs_exist_ok=True)
print('Private originals and audit evidence retained locally; never a public upload target')
