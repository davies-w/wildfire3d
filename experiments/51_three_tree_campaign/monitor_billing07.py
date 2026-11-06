"""Refresh the private project spending estimate while the November continuation runs."""
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import json
import math
import os
import subprocess
import sys
import time

from cloud07 import G, P, PROJECT, R, gc, save


def utc_seconds(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()


def main():
    prior = json.loads((P / "resume3-drained-pairs.json").read_text())
    start = json.loads((P / "resume4b-execution.json").read_text())["startTime"]
    billing = json.loads((P / "posted-nov06.json").read_text())
    source = billing["source"]
    assert source.startswith(PROJECT + ".billing_export.") and "`" not in source
    # Use a single query snapshot for the charge total and its VM-hour coverage.
    query = f"""
      WITH costs AS (
        SELECT resource.name AS resource, sku.description AS sku, usage_start_time AS hour,
               usage_end_time AS finish,
               cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c),0) AS net, currency
        FROM `{source}`
        WHERE project.id='{PROJECT}' AND usage_start_time>=TIMESTAMP('2026-10-01')
          AND usage_start_time<CURRENT_TIMESTAMP()
      )
      SELECT (SELECT SUM(net) FROM costs) AS posted, (SELECT ARRAY_AGG(DISTINCT currency) FROM costs) AS currencies,
             ARRAY(SELECT DISTINCT AS STRUCT resource, sku, hour, finish FROM costs
                   WHERE hour>=TIMESTAMP('2026-11-05') AND REGEXP_CONTAINS(resource,r't51r07-c[0-9]+-')
                   AND (sku LIKE '%C3 Instance Core%' OR sku LIKE '%C3 Instance Ram%')) AS coverage
    """
    sdk = os.path.dirname(G)
    command = [sdk + "/bq", "--project_id=" + PROJECT, "--location=US", "--format=json", "query",
               "--use_legacy_sql=false", "--maximum_bytes_billed=1000000000", query]
    row, = json.loads(subprocess.check_output(command, text=True, env=dict(os.environ, PATH=sdk+":"+os.environ["PATH"])))
    assert row["currencies"] == ["USD"]
    posted = Decimal(row["posted"])
    coverage = defaultdict(set)
    for item in row["coverage"]:
        hour = int(utc_seconds(item["hour"]))
        assert utc_seconds(item["finish"]) == hour + 3600
        coverage[item["resource"].split("/")[-1], hour].add("core" if " Core " in item["sku"] else "ram")

    log_filter = ('protoPayload.serviceName="compute.googleapis.com" AND protoPayload.resourceName=~"/instances/t51r07-c[0-9]+-" '
                  'AND ((protoPayload.methodName:"instances.insert" AND operation.first=true) OR '
                  '(protoPayload.methodName:"instances.delete" AND operation.last=true)) AND timestamp>="'+start+'"')
    events = gc("logging", "read", log_filter, "--limit=10000")
    assert len(events) < 10000
    for event in events:
        payload = event["protoPayload"]
        vm = payload["resourceName"].split("/zones/")[1]
        pair = prior.setdefault(vm, {"insert": [], "delete": []})
        key = "insert" if payload["methodName"].endswith(".insert") else "delete"
        pair[key].append(utc_seconds(event["timestamp"]))
    observed = time.time()
    missing = 0
    for vm, pair in prior.items():
        start = min(pair["insert"])
        finish = max(pair["delete"]) if pair["delete"] else observed
        for hour in range(math.floor(start/3600)*3600, math.ceil(finish/3600)*3600, 3600):
            if coverage[vm.split("/")[-1], hour] != {"core", "ram"}:
                missing += min(finish, hour+3600) - max(start, hour)
    estimate = float(posted) + missing*.15/3600
    ceiling = json.loads((P / "nov06-billing-reconciliation.json").read_text())["simulation_ceiling_usd"]
    save("nov06-monitor-reconciled.json", dict(posted=float(posted), unposted_compute=missing*.15/3600,
         estimate=estimate, within_ceiling=estimate<ceiling, observed_at=observed))
    print("Current estimate within ceiling:", estimate < ceiling)
    assert estimate < ceiling


if __name__ == "__main__":
    main()
