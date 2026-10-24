from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;(R/'data').mkdir(exist_ok=True);(R/'results').mkdir(exist_ok=True)
shutil.copyfile(R.parent/'attempt15/data/sequences.npz',R/'data/sequences.npz')
s=json.loads((R.parent/'attempt15/schema.json').read_text());s['comparison']='Same three physical states/splits; GRU adds32 internal latent values, no additional measured states'
(R/'schema.json').write_text(json.dumps(s,indent=2))
