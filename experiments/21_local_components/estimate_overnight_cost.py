"""Conservative compute-only proxy from workflow lifetimes; not billing export."""
import datetime,json,time
from scene import ROOT
b=json.loads((ROOT/'budget-overnight.json').read_text());rows=[]
for name,r in b['reservations'].items():
 p=ROOT/'jobs'/name/'status.json';s=json.loads(p.read_text()) if p.exists() else {};duration=s.get('duration');known=duration is not None
 seconds=float(duration.rstrip('s')) if known else r['vm_hours']*3600
 rows.append(dict(case=name,workflow_state=s.get('state'),seconds_used_for_proxy=seconds,basis='entire completed workflow lifetime, including setup/cleanup' if known else 'full reserved VM lifetime, not measured usage',compute_usd_at_ceiling=seconds/3600*.08))
out=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reserved_usd=b['reserved_usd'],authorized_usd=b['authorized_usd'],compute_only_conservative_proxy_usd=sum(r['compute_usd_at_ceiling'] for r in rows),rows=rows,rate_ceiling_usd_per_vm_hour=.08,source='results/sampling-price.json reports0.079528USD/VMh checked2026-10-18; reservations use0.08 ceiling.',limitations='Not an invoice or confirmed billed spend. Includes whole workflow time as if one VM existed throughout and full reserved lifetime for unfinished jobs. Excludes storage,network,logs,workflow charges,taxes. The unrecycled7.70USD reservation remains the conservative all-in authorization accounting.')
(ROOT/'results/overnight-cost-proxy.json').write_text(json.dumps(out,indent=2));print('Compute-only proxy including unfinished full lifetime:',round(out['compute_only_conservative_proxy_usd'],3),'USD; reservations',out['reserved_usd'])
