from pathlib import Path
import shutil
R=Path(__file__).parent
(R/'data/initial').mkdir(parents=True,exist_ok=True)
for n in ['cases.json','groups.json','data/geometries.npz']:shutil.copy2(R.parent/'attempt03'/n,R/n)
shutil.copy2(R.parent/'attempt03/data/collected/single-epoch-080.pt',R/'data/initial/single.pt')
