"""Measured solver runtimes; separate CPU seconds from elapsed time."""
import json,numpy as np
from pathlib import Path
R=Path(__file__).parent
rows=[]
for p in sorted((R/'data/cloud').glob('*/result.json')):
 r=json.loads(p.read_text());rows.append({k:r[k] for k in ['case','split','wall_seconds','cpu_user_s','cpu_system_s','physical_seconds_reached','full_horizon']})
report=dict(cases=rows,by_split={})
for split in sorted({r['split'] for r in rows}):
 a=[r for r in rows if r['split']==split]
 report['by_split'][split]=dict(count=len(a),wall_seconds_min_median_max=np.quantile([r['wall_seconds'] for r in a],[0,.5,1]).tolist(),CPU_seconds_min_median_max=np.quantile([r['cpu_user_s']+r['cpu_system_s'] for r in a],[0,.5,1]).tolist())
(R/'results/runtime-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['by_split'],indent=2))
