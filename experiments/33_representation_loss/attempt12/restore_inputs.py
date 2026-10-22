from pathlib import Path
import shutil
r=Path(__file__).parent
(r/'data/resume').mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'../attempt11/data/resume/current.pt',r/'data/resume/current.pt')
for a in ['control','dose_background','physical_low']:shutil.copy2(r/f'../attempt11/data/collected/{a}-checkpoint-2500.pt',r/f'data/resume/{a}.pt')
