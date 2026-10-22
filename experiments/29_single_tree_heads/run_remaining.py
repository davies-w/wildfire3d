"""Sequential local-only work, no retries and no cloud commands."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).parent
assert (R/'data/models/bounded.pt').exists()
subprocess.run([sys.executable,str(R/'train.py'),'heads','--steps','3200'],check=True)
for n in ['previous','bound_only','bounded','heads','strength_only','interpolation']:subprocess.run([sys.executable,str(R/'evaluate.py'),n],check=True)
print('ALL_LOCAL_COMPARISONS_DONE',flush=True)
