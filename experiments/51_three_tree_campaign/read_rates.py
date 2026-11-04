"""Read bounded posted C3 SKU usage/rates; private evidence, no ledger mutation."""
from pathlib import Path
import json,os,subprocess
R=Path(__file__).resolve().parent
sdk=Path.home()/'.local/google-cloud-sdk/bin'
q="""SELECT sku.id, sku.description, usage.pricing_unit, currency,
 SUM(cost) gross_cost, SUM(usage.amount_in_pricing_units) usage_quantity,
 MIN(usage_start_time) first_usage, MAX(usage_end_time) last_usage
FROM `tmrw-wildfire-20261015.billing_export.gcp_billing_export_resource_v1_0136FB_EBB956_005416`
WHERE project.id='tmrw-wildfire-20261015' AND usage_start_time>=TIMESTAMP('2026-11-01')
 AND sku.description LIKE 'Spot Preemptible C3 Instance %'
GROUP BY 1,2,3,4"""
p=subprocess.run([str(sdk/'bq'),'--project_id=tmrw-wildfire-20261015','--location=US','--format=json','query','--use_legacy_sql=false','--maximum_bytes_billed=1000000000',q],env=dict(os.environ,PATH=str(sdk)+os.pathsep+os.environ.get('PATH','')),capture_output=True,text=True,check=True)
d=json.loads(p.stdout);(R/'private/c3-posted-rates.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
