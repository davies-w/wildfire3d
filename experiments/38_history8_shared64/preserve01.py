from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;out=R/'data/provenance01';out.mkdir(exist_ok=True)
for p in (R/'results01').glob('*.json'):shutil.copy2(p,out/p.name)
for p in (R/'results').glob('scorecard-layout*.json'):shutil.copy2(p,out/p.name)
shutil.copy2(R.parent/'33_representation_loss/budget.json',out/'budget.json')
shutil.copy2(R/'README.md',out/'README.md')
