"""Preserve private control-plane and financial evidence; local mirror only."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;D=R/'data/provenance';D.mkdir(parents=True,exist_ok=True)
shutil.copytree(R/'results',D/'results',dirs_exist_ok=True)
shutil.copy2(R.parent/'33_representation_loss/budget.json',D/'budget.json')
for candidate in ['or','ia','sc']:
 for stem in ['progress','startup-audit-']:
  src=R/('data/'+stem+candidate)
  if src.exists():shutil.copytree(src,D/(stem+candidate),dirs_exist_ok=True)
print('Private evidence preserved; do not include this output in public artifact sync')
