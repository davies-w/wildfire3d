"""Conservative elapsed-controller cost estimates, not invoice-verified billing."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ledger=json.loads((ROOT/'budget.json').read_text());rows=[]
for reservation in ledger['reservations']:
    folder=ROOT/'batches'/reservation['batch'];spec=json.loads((folder/'batch.json').read_text());status=json.loads((folder/'results/status.json').read_text())
    assert status['state']=='SUCCEEDED'
    cleanup=json.loads((folder/'results/cleanup.json').read_text());assert not any(cleanup.values())
    seconds=float(status['duration'].rstrip('s'));compute=seconds/3600*.065744
    row=dict(batch=reservation['batch'],controller_elapsed_s=seconds,compute_upper_estimate_usd=compute,ancillary_allowance_usd=spec['ancillary_allowance_usd'],conservative_total_estimate_usd=compute+spec['ancillary_allowance_usd'],reserved_usd=reservation['allowance_usd'],billing_invoice_verified=False)
    (folder/'results/cost.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
report=dict(batches=rows,reserved_total_usd=sum(r['reserved_usd'] for r in rows),compute_upper_estimate_usd=sum(r['compute_upper_estimate_usd'] for r in rows),conservative_total_estimate_usd=sum(r['conservative_total_estimate_usd'] for r in rows),billing_invoice_verified=False,cloud_compute_cleanup_verified=True)
(ROOT/'results/cost-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
