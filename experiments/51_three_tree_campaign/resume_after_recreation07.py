"""Continue fresh indices once after the confirmed infrastructure interruption drains."""
from datetime import datetime
import json
import re
import subprocess
import sys
import time

import requests

from cloud07 import B, BUCKET, G, P, PREFIX, R, WF, fcntl, gc, save


def read(name):
    return json.loads((P / name).read_text())


def refresh(script):
    subprocess.run([sys.executable, str(R / script)], check=True, stdout=subprocess.DEVNULL)


def assert_empty():
    for args in [("batch","jobs","list","--location=us-central1"), ("compute","instances","list"),
                 ("compute","disks","list")]:
        assert not gc(*args, "--filter=name~t51r07")
    for suffix in ("-nov-case","-nov-epoch","-nov2-case","-nov2-epoch","-resume5"):
        for state in ("ACTIVE","QUEUED"):
            assert not gc("workflows","executions","list",WF+suffix,"--location=us-central1","--filter=state="+state)


def run():
    assert not (P/"resume5-submission-intent.json").exists()
    refresh("monitor_campaign07.py")
    old = read("status.json")
    assert old["controller"]["name"] == read("resume4b-execution.json")["name"]
    if old["controller"]["state"] == "ACTIVE":
        print("Waiting for the original controller to drain", flush=True)
        return False
    assert old["controller"]["state"] == "SUCCEEDED"
    state = json.loads(old["controller"]["result"])["state"]
    assert state["stopped"] and not state["audit_required"] and not state["active"]
    assert_empty()
    refresh("inspect_outputs07.py")
    refresh("monitor_billing07.py")
    assert read("nov06-monitor-reconciled.json")["within_ceiling"]
    assert read("nov2-check-result.json")["state"] == "SUCCEEDED"
    names = [v["name"][len(PREFIX):] for v in read("objects.json")]
    def indices(pattern):
        return {int(m[1]) for n in names if (m := re.fullmatch(pattern,n))}
    cursor = state["cursor"]
    assert indices(r"claims/wave-(\d+)\.json") == indices(r"children/(\d+)\.json") == set(range(cursor))
    assert max(indices(r"epochs/(\d+)/claim.json")) < state["epoch"]
    proofs = read("worker-proofs.json")
    outcomes = [v["proof"] for v in proofs if v["name"].startswith(PREFIX+"outcomes/") and
                int(v["name"].rsplit("/",1)[1].split(".")[0]) >= 586]
    assert len(outcomes) == cursor-586 and all(o["cleanup_verified"] for o in outcomes)
    unknown = [o["wave"] for o in outcomes if not (o["passed"] or o["spot"] or o.get("admission_deferred"))]
    assert unknown == ["wave-000824"]
    step = next(v["proof"] for v in proofs if v["name"] == PREFIX+"wave-000824/failed-task.json")
    events = step["tasks"][0]["status"]["statusEvents"]
    assert any(e.get("taskExecution",{}).get("exitCode")==50006 and "VM is recreated during task execution" in e.get("description","") for e in events)
    assert state["completed"] == 1022 + sum(o["passed"] for o in outcomes)
    assert state["spent"] + state["reserve"] <= state["limit"] and state["policy"] in (180,300)
    assert time.time() < datetime.fromisoformat("2026-11-08T17:16:41+00:00").timestamp() - 12600  # original permission end minus full job bound
    state["stopped"] = False
    state["interrupted"] += 1
    payload = dict(state=state, predecessor=old["controller"]["name"], excluded_infrastructure_case=824)
    token = subprocess.check_output([G,"auth","print-access-token"],text=True).strip()
    with (B.parent/"data/budget.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger = json.loads(B.read_text())
        entry = ledger["reservations"]["fds-tree51-nov06-continuation"]
        assert entry["state"]=="submitted" and ledger["reservations"]["fds-tree51-training"]["allowance_usd"]==20
        assert state["limit"] <= round(entry["compute_limit_usd"]*1e6)
        assert ledger["estimated_spend_usd"] + entry["allowance_usd"] <= entry["spending_ceiling"] == 180
        headers = {"Authorization":"Bearer "+token, "Content-Type":"application/json"}
        contents = json.dumps(payload).encode()
        response = requests.post("https://storage.googleapis.com/upload/storage/v1/b/"+BUCKET+"/o",
            params=dict(uploadType="media",name=PREFIX+"control/continuation-5.json",ifGenerationMatch=0),
            headers=headers,data=contents,timeout=60)
        response.raise_for_status()
        check = requests.get("https://storage.googleapis.com/storage/v1/b/"+BUCKET+"/o/"+requests.utils.quote(PREFIX+"control/continuation-5.json",safe=""),
            params=dict(alt="media",generation=response.json()["generation"]),headers=headers,timeout=60)
        check.raise_for_status()
        assert check.content == contents
        save("resume5-state.json",payload)
        with (P/"resume5-submission-intent.json").open("x") as intent:
            json.dump(dict(time=time.time(),cursor=cursor,workflow=WF+"-resume5"),intent)
        e = gc("workflows","execute",WF+"-resume5","--location=us-central1","--data={}")
        save("resume5-execution.json",e)
        entry.setdefault("continuations",[]).append(e["name"])
        tmp = B.with_suffix(".resume5.tmp")
        tmp.write_text(json.dumps(ledger,indent=2)+"\n")
        tmp.replace(B)
    record = json.loads((R/"continuation-record07.json").read_text())
    record["previous_november_continuation"] = record["latest_continuation"]
    record["latest_continuation"] = dict(workflow=WF+"-resume5",execution=e["name"].split("/")[-1],
        created_at=e["startTime"],first_index=cursor,remaining_never_submitted=state["total"]-cursor,
        excluded_vm_recreation=824,local_admission_gate=False)
    (R/"continuation-record07.json").write_text(json.dumps(record,indent=2)+"\n")
    print("Submitted unique continuation",cursor,flush=True)
    return True


if __name__ == "__main__":
    with (P/"resume5-watch.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for tick in range(375):
            if run():
                break
            time.sleep(30)
        else:
            raise TimeoutError("Drain exceeded bounded watch")
