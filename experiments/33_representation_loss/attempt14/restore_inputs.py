from pathlib import Path
import shutil
r=Path(__file__).parent
(r/'data/resume').mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'../attempt13/data/collected/expanded120-checkpoint-6000.pt',r/'data/resume/current.pt')
