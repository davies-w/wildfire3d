"""Subtract already-posted in-window bucket downloads from one remaining transfer envelope."""
from pathlib import Path
from decimal import Decimal
import datetime,fcntl,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,B,save
KEY='density36-raw-verification-transfer';BUCKET='tmrw-wildfire-20261015-trial';SKU='Download Worldwide Destinations (excluding Asia & Australia)'
def utc(x):
 value=datetime.datetime.fromisoformat(x.replace(' UTC','+00:00').replace('Z','+00:00'));return value.replace(tzinfo=datetime.timezone.utc) if value.tzinfo is None else value.astimezone(datetime.timezone.utc)
def posted_overlap(rows,start):
 matched=[]
 for r in rows:
  if r['service']!='Cloud Storage' or r['sku']!=SKU or r.get('resource_name')!=BUCKET:continue
  assert r['currency']=='USD' and r['cost_type']=='regular'
  # A date-aggregated row crossing the reservation start is excluded completely.
  if utc(r['first_usage_start'])<start:continue
  assert utc(r['last_usage_end'])>=utc(r['first_usage_start'])
  matched.append(r)
 total=sum((Decimal(str(r['net_cost'])) for r in matched),Decimal(0));assert total>=0
 return total,matched

def main():
 p=R/'data/billing-export-canonical03.json';snapshot=json.loads(p.read_text());assert snapshot['project']=='tmrw-wildfire-20261015' and snapshot['status']=='posted_costs_subject_to_adjustment';rows=snapshot['costs'];total=sum((Decimal(str(r['net_cost'])) for r in rows),Decimal(0))
 with (B.parent/'data/budget.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads(B.read_text());r=b['reservations'][KEY];assert r['state']=='reserved_before_upload'
  assert abs(total-Decimal(str(b['accounting']['project_posted_comparison_usd'])))<Decimal('.000001'),'Snapshot must already be included in project accounting'
  assert Decimal(str(b['estimated_spend_usd']))>=total
  original=Decimal(str(r.get('original_allowance_usd',r['allowance_usd'])));assert original==20
  start=datetime.datetime.fromtimestamp(r['reserved_unix'],datetime.timezone.utc);overlap,matched=posted_overlap(rows,start);remaining=max(Decimal(0),original-overlap)
  # Preserve all other allowances, especially the separate40USD Flex commitment.
  before={k:dict(v) for k,v in b['reservations'].items() if k!=KEY};old_spend=b['estimated_spend_usd']
  r.update(original_allowance_usd=float(original),allowance_usd=float(remaining),posted_download_overlap_usd=float(overlap),accounting_stage='remaining_envelope_after_already_posted_downloads',posted_snapshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),scope='Remaining part of original20USD maximum for total campaign bucket downloads/operations within160GiB. Already-posted exact bucket Download Worldwide SKU rows wholly after reservation start consume the envelope; mixed first-day row and operation charges are not deducted. Bucket/time accounting, not per-object billing attribution.')
  b['reserved_usd']=sum(v['allowance_usd'] for v in b['reservations'].values() if v['state'] in ['reserved_before_upload','submission_pending','submitted','delegated_to_cloud_queue'])
  assert b['estimated_spend_usd']==old_spend and all(b['reservations'][k]==v for k,v in before.items())
  assert b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']
  B.write_text(json.dumps(b,indent=2)+'\n')
 proof=dict(passed=True,original_envelope_usd=float(original),already_posted_overlap_usd=float(overlap),remaining_envelope_usd=float(remaining),spend_unchanged=True,other_reservations_unchanged=True,matched_posted_rows=matched,snapshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),estimated_spend_usd=b['estimated_spend_usd'],reserved_usd=b['reserved_usd'],headroom_usd=b['authorized_usd']-b['estimated_spend_usd']-b['reserved_usd'],limitations=r['scope']+' Posted charges remain subject to adjustment. Remaining allowance retains operations cushion and unposted transfer risk; byte-cap checks still apply before transfers.')
 save('results/canonical-transfer-reservation-reconciled.json',proof);print(json.dumps({k:v for k,v in proof.items() if k!='matched_posted_rows'},indent=2))
if __name__=='__main__':main()
