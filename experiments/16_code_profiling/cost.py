"""Estimate resource charges from lifecycle duration; not an invoice or dollar cap."""
from datetime import datetime
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
build=json.loads((ROOT/'results/build-status.json').read_text());workflow=json.loads((ROOT/'results/workflow-status.json').read_text())
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
build_s=(dt(build['finishTime'])-dt(build['startTime'])).total_seconds()
if workflow['state']=='ACTIVE':raise RuntimeError('Wait for final lifecycle timestamps')
controller_s=(dt(workflow['endTime'])-dt(workflow['startTime'])).total_seconds()
# Workflow duration deliberately includes provisioning and cleanup, overestimating VM runtime.
result={'invoice_confirmed':False,'build_seconds':build_s,'controller_seconds':controller_s,'build_rate_usd_per_minute':.006,'c3_spot_rate_usd_per_hour':.065744,'build_estimate_usd_before_credits':build_s/60*.006,'worker_estimate_usd_before_credits':controller_s/3600*.065744,'other_charges_allowance_usd':.13,'approved_total_allowance_usd':.45,'sources':['https://cloud.google.com/build/pricing','https://cloud.google.com/spot-vms/pricing?hl=en'],'caveat':'Rate-based estimate, not posted billing. Worker duration includes controller overhead. Other-charge allowance covers disk, IP, storage, downloads, and control/logging; it is not a measured charge. No free-tier credits assumed.'}
result['estimated_compute_usd_before_credits']=result['build_estimate_usd_before_credits']+result['worker_estimate_usd_before_credits']
result['compute_plus_other_allowance_usd']=result['estimated_compute_usd_before_credits']+.13
(ROOT/'results/cost.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
