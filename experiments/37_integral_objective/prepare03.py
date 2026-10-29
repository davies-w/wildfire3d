from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;D=R/'data/training03'
for n in ['worker.py','model.py','plain_model.py','gated_model.py','objective.py','schema.json','runtime.py','coverage-plan.json','data/sequences.npz']:
 (D/n).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'data/training02'/n,D/n)
p=D/'runtime.py';p.write_text(p.read_text().replace('integral37/training02/','integral37/training03/'))
