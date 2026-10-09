"""Extract EC2 pricing for compute-optimised families from the Vantage dump.

Prints, per instance, the on-demand hourly price, vCPU count, and price per
vCPU-hour, so families can be compared on a per-core basis rather than a
per-instance basis.  Also computes an 8-core-equivalent cost for a 4-hour job.
"""
import json

WANT = ("c7i.", "c7a.", "c7g.", "c8g.", "c6a.", "c6i.", "m7i.", "m7a.")
JOB_HOURS = 4.0

d = json.load(open("/tmp/ec2.json"))
rows = []
if isinstance(d, dict):
    d = list(d.values())
for i in d:
    it = i.get("instance_type", "")
    if not it.startswith(WANT):
        continue
    v = i.get("vCPU")
    if v in (None, 0) or v > 64:
        continue
    od = i.get("pricing", {}).get("us-east-1", {}).get("linux", {}).get("ondemand")
    if not od:
        continue
    rows.append((float(od) / v, it, v, float(od), i.get("memory")))

rows.sort()
print("%-16s %4s %9s %11s %9s" % ("instance", "vCPU", "$/hr", "$/vCPU-hr", "job $"))
for pc, it, v, od, mem in rows:
    if 4 <= v <= 32:
        print("%-16s %4d %9.3f %11.5f %9.2f"
              % (it, v, od, pc, od * JOB_HOURS))
