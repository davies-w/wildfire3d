"""Conservative compute proxy from controller lifetime; not invoice spend."""
from pathlib import Path
from datetime import datetime
import json
R=Path(__file__).parent
rows=[]
for p,rate in [(R.parent/'30_tree_sequence/results/status.json',.8),(R/'results/gpu-status.json',.8)]+[(p,.08) for p in (R/'jobs').glob('*/status.json')]:
 d=json.loads(p.read_text());assert d.get('endTime'),str(p);seconds=(datetime.fromisoformat(d['endTime'].replace('Z','+00:00'))-datetime.fromisoformat(d['startTime'].replace('Z','+00:00'))).total_seconds();rows.append(dict(source=str(p.relative_to(R.parent)),controller_lifetime_s=seconds,conservative_vm_rate_usd_hour=rate,compute_proxy_usd=seconds/3600*rate))
 out=dict(rows=rows,total_compute_proxy_usd=sum(x['compute_proxy_usd'] for x in rows),reserved_usd=1+json.loads((R/'budget.json').read_text())['reserved_usd'],ceiling_usd=3.5,interpretation='Uses full controller elapsed time, including queue and cleanup, at conservative whole-VM budget rates. Excludes storage, network and ancillary services. Not billed spend or a total-cost guarantee. Reservations were not recycled.')
 (R/'results/cost-proxy.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
