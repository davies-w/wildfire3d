from pathlib import Path
import shutil
R=Path(__file__).parent
(R/'data').mkdir(exist_ok=True)
for n in ['cases.json','groups.json','coverage-plan.json','data/geometries.npz']:shutil.copy2(R.parent/n,R/n)
