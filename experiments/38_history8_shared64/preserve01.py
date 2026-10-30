from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;out=R/'data/provenance01';out.mkdir(exist_ok=True)
for folder in ['results01','results02','results03','results04','results05','results06']:
 for p in (R/folder).glob('*.json'):shutil.copy2(p,out/(folder+'-'+p.name))
for p in (R/'results').glob('scorecard-layout*.json'):shutil.copy2(p,out/p.name)
shutil.copy2(R.parent/'33_representation_loss/budget.json',out/'budget.json')
shutil.copy2(R/'README.md',out/'README.md')

if (R/'results01/preemption-audit.json').exists():shutil.copy2(R/'results01/preemption-audit.json',out/'preemption-audit.json')
