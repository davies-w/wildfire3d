import shutil,json
from pathlib import Path
r=Path(__file__).parent
(r/"data/resume").mkdir(parents=True,exist_ok=True)
for n,p in {'spatial_heads.pt': '../data/collected/spatial_heads-checkpoint-600.pt', 'current.pt': '../data/collected/current-checkpoint-600.pt', 'loss_only.pt': '../data/collected/loss_only-checkpoint-600.pt'}.items():shutil.copy2(r/p,r/"data/resume"/n)
