import shutil,json
from pathlib import Path
r=Path(__file__).parent
(r/"data/resume").mkdir(parents=True,exist_ok=True)
for n,p in {'spatial_heads.pt': '../attempt03/data/collected/spatial_heads-checkpoint-6000.pt', 'current.pt': '../attempt02/data/collected/current-checkpoint-6000.pt', 'loss_only.pt': '../attempt03/data/collected/loss_only-checkpoint-6000.pt'}.items():shutil.copy2(r/p,r/"data/resume"/n)
