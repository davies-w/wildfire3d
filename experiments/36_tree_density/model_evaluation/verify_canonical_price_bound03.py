"""Verify the conservative bound against exact G2-standard-4 hourly entries on Google's pricing page."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,urllib.request
R=Path(__file__).resolve().parents[1]

u='https://cloud.google.com/products/compute/pricing/accelerator-optimized'
s=urllib.request.urlopen(u,timeout=60).read();html=s.decode();prices=[];excerpts=[]
for m in re.finditer(r'g2-standard-4(?![0-9])',html):
 window=html[m.start():m.start()+1000];rate=re.search(r'\$([0-9]+(?:\.[0-9]+)?) / 1 hour',window)
 if rate:prices.append(float(rate.group(1)));excerpts.append(window[:rate.end()])
assert prices and min(prices)>.1 and max(prices)<=1.2,(len(prices),min(prices) if prices else None,max(prices) if prices else None)
plan=json.loads((R/'results/canonical-trial-plan.json').read_text())['budget_plan'];assert plan['maximum_rate_bound_usd_per_hour']==1.2 and plan['maximum_allowance_usd']==1.3;assert (plan['workflow_cap_s']+plan['shutdown_margin_s'])*1.2/3600<=1.3
proof=dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=u,source_sha256=hashlib.sha256(s).hexdigest(),source_bytes=len(s),exact_machine_hourly_entries=len(prices),extracted_min_usd_per_hour=min(prices),extracted_max_usd_per_hour=max(prices),extracted_prices=prices,source_excerpts=excerpts,conservative_rate_bound_usd_per_hour=1.2,maximum_compute_allowance_usd=1.3,scope='USD per-hour G2-standard-4 entries exposed by the official pricing page. Exact machine boundary excludes G2-standard-48. Shared storage/network/workflow charges remain project-level, not zero. No purchase or compute performed.')
(R/'results/canonical-pilot03-price-bound.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ['source_excerpts','extracted_prices']},indent=2))
