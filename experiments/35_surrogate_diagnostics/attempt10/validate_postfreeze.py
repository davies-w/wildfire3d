"""Additional local checks of immutable package inputs; no optimizer or training."""
from pathlib import Path
import hashlib,json,torch
from model import encode,physical
from metrics import statistics
R=Path(__file__).parent
w=torch.tensor([1.,5.])[:,None,None,None];a=torch.zeros(2,6,8,8,8);a[:,0]=20;a[:,2]=w;a[:,1,0,0,0]=3;a[:,0,0,0,0]=100
e=encode(a,w);assert torch.allclose(physical(e,w),a,atol=1e-5);v=statistics(e,e,a,w,torch.ones(6));assert v.shape==(2,31)
freeze=json.loads((R/'results/input-freeze.json').read_text())
for n,h in freeze.items():
 with (R/n).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
(R/'results/postfreeze-check.json').write_text(json.dumps(dict(passed=True,frozen_files=len(freeze),batched_wind_roundtrip=True,statistics_columns=31,scope='CPU synthetic calculations and read-only hashes; no training. Local continuation scripts added outside frozen cloud package.'),indent=2)+'\n')
