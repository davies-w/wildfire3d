"""Independent field-history check against FDS global HRR output."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).parent;rows=[]
for c in json.loads((R/'cases.json').read_text()):
 if c['split']!='test':continue
 name=c['case'];p=R/f'data/cloud/{name}/{name}_hrr.csv'
 if not p.exists():continue
 with p.open() as f:raw=list(csv.reader(f))
 keys=[x.strip().strip('"') for x in raw[1]];v=np.array(raw[2:],float);idx=keys.index('HRR');t=np.load(R/f'data/test-fields/{name}-time.npy');a=np.load(R/f'data/test-fields/{name}.npy',mmap_mode='r');q=np.array(a[:,1]).sum((1,2,3))*.125;truth=np.interp(t,v[:,0],v[:,idx]);active=truth>10
 rows.append(dict(case=name,field_integral_peak_kW=float(q.max()),global_HRR_peak_kW=float(v[:,idx].max()),active_relative_L1=float(abs(q[active]-truth[active]).sum()/truth[active].sum()) if active.any() else None,note='Instantaneous2s field snapshots vs interpolated global HRR output; differing output averaging/cadence means not expected to be identical.'))
(R/'results/field-hrr-crosscheck.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
