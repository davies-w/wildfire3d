"""Preserve private control-plane and financial evidence; local mirror only."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;D=R/'data/provenance';D.mkdir(parents=True,exist_ok=True)
shutil.copytree(R/'results',D/'results',dirs_exist_ok=True)
shutil.copy2(R.parent/'33_representation_loss/budget.json',D/'budget.json')
print('Private evidence preserved; do not include this output in public artifact sync')
