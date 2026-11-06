"""Combine posted project charges with VM allocation intervals still missing from the export."""
import math
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import json

from cloud07 import P, save


def timestamp(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()


def reconcile():
    posted = json.loads((P / "posted-nov06.json").read_text())
    assert posted["status"] == "posted_costs_subject_to_adjustment" and posted["costs"]
    assert all(row["currency"] == "USD" for row in posted["costs"])
    net = sum(Decimal(row["net_cost"]) for row in posted["costs"])
    coverage = defaultdict(set)
    for row in json.loads((P / "billing-hour-coverage-nov06.json").read_text()):
        vm = row["resource"].split("/")[-1]
        hour = int(timestamp(row["start_time"]))
        assert int(timestamp(row["end_time"])) == hour + 3600
        coverage[vm, hour].add("core" if " Core " in row["sku"] else "ram")
    missing = defaultdict(float)
    pairs = json.loads((P / "resume3-drained-pairs.json").read_text())
    for name, allocation in pairs.items():
        start, end = min(allocation["insert"]), max(allocation["delete"])
        first_hour = math.floor(start / 3600) * 3600
        for hour in range(first_hour, math.ceil(end / 3600) * 3600, 3600):
            present = coverage[name.split("/")[-1], hour]
            assert present in (set(), {"core", "ram"}), "Partial SKU coverage requires separate reconciliation"
            if not present:
                missing[datetime.fromtimestamp(hour, timezone.utc).date().isoformat()] += min(end, hour+3600) - max(start, hour)
    unposted = sum(missing.values()) * .15 / 3600
    baseline = float(net) + unposted
    result = dict(posted_net_usd=float(net), missing_seconds_by_utc_date=missing,
                  unposted_compute_usd=unposted, cumulative_estimate_usd=baseline,
                  simulation_ceiling_usd=180, training_protected_usd=20,
                  additional_project_headroom_usd=180-baseline, billing_as_of=posted["fetched_at_utc"])
    save("nov06-billing-reconciliation.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    reconcile()
