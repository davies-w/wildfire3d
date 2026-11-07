"""Recover from a missing trial input using actual child executions, without replaying a case."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import math
import subprocess
import sys
import time

import requests

from cloud07 import B, BUCKET, G, P, PREFIX, R, WF, fcntl, gc, save


def read(name):
    return json.loads((P/name).read_text())


def inspect_workflow(suffix):
    name=WF+suffix
    entries=gc("workflows","executions","list",name,"--location=us-central1","--limit=100")
    assert len(entries)<100
    def full(entry):
        return gc("workflows","executions","describe",entry["name"].split("/")[-1],"--workflow="+name,"--location=us-central1")
    with ThreadPoolExecutor(6) as pool:
        return list(pool.map(full,entries))


def check_empty():
    for args in [("batch","jobs","list","--location=us-central1"),("compute","instances","list"),("compute","disks","list")]:
        if gc(*args,"--filter=name~t51r07"):
            return False
    return True


def refreshed(script):
    subprocess.run([sys.executable,str(R/script)],check=True,stdout=subprocess.DEVNULL)


def readiness():
    if (P/"nov3-readiness.json").exists():
        assert read("nov3-readiness.json")["passed"]
        return
    e=gc("workflows","execute",WF+"-nov3-check","--location=us-central1")
    for _ in range(90):
        x=gc("workflows","executions","describe",e["name"].split("/")[-1],"--workflow="+WF+"-nov3-check","--location=us-central1")
        if x["state"] not in ("ACTIVE","QUEUED"):
            break
        time.sleep(2)
    assert x["state"]=="SUCCEEDED",x.get("error",{}).get("context")
    names=json.loads(x["result"])["children"]
    assert len(names)==3
    for name in names:
        parts=name.split("/")
        child=gc("workflows","executions","describe",parts[-1],"--workflow="+parts[-3],"--location=us-central1")
        assert child["state"]=="SUCCEEDED" and json.loads(child["result"])["dry_run"]
    save("nov3-readiness.json",dict(passed=True,execution=x))


def settle():
    assert not (P/"resume6-submission-intent.json").exists()
    failed=read("nov2-epoch-failure.json")
    err=json.loads(failed["error"]["payload"])
    assert err["code"]==404 and "inputs/items/858.json" in err["body"]
    assert read("restaged-inputs858.json")["passed"]
    if not check_empty():
        return False
    cases=inspect_workflow("-nov2-case")
    if any(x["state"] in ("ACTIVE","QUEUED") for x in cases):
        return False
    cases=[x for x in cases if not json.loads(x["argument"]).get("dry_run")]
    assert len(cases)==21 and {json.loads(x["argument"])["index"] for x in cases}==set(range(837,858))
    assert all(x["state"]=="SUCCEEDED" for x in cases)
    state=read("resume5-state.json")["state"]
    assert state["cursor"]==837 and not state["active"]
    epochs=[x for x in inspect_workflow("-nov2-epoch") if not json.loads(x["argument"]).get("dry_run")]
    assert len([x for x in epochs if x["state"]=="FAILED"])==1 and all(x["state"] in ("FAILED","SUCCEEDED") for x in epochs)
    state["epoch"]=1+max(json.loads(x["argument"])["state"]["epoch"] for x in epochs)
    outcomes={}
    for child in cases:
        i=json.loads(child["argument"])["index"]
        o=json.loads(child["result"])
        assert o["wave"]==f"wave-{i:06d}" and o["cleanup_verified"] and o["count"]==1
        charge=math.ceil(o["compute_charge_upper_usd"]*1e6)
        assert 0<=charge<=state["reserve"]
        state["spent"]+=charge
        state["started"]+=int(o["started"])
        state["completed"]+=int(o["passed"])
        if not o["passed"]:
            assert o["spot"] or o.get("vm_recreated") or o.get("admission_deferred")
            state["interrupted"]+=1
            state["evicted"]+=int(o["spot"])
        outcomes[i]=o
    save("drained-storage-outcomes.json",outcomes)
    state["cursor"]=858
    if state["evicted"]>=4 and state["evicted"]*10>=state["started"]:
        assert state["policy"]==180, "Verify policy publication before continuing"
    assert state["spent"]+state["reserve"]<=state["limit"]
    assert not state["stopped"] and not state["audit_required"]
    assert time.time()<datetime.fromisoformat("2026-11-08T17:16:41+00:00").timestamp()-12600
    readiness()
    refreshed("monitor_billing07.py")
    assert read("nov06-monitor-reconciled.json")["within_ceiling"]
    # Validate data, live ownership, and lack of an earlier next-index submission.
    t=subprocess.check_output([G,"auth","print-access-token"],text=True).strip()
    headers={"Authorization":"Bearer "+t,"Content-Type":"application/json"}
    url="https://storage.googleapis.com/storage/v1/b/"+BUCKET+"/o/"
    def get(name):
        return requests.get(url+requests.utils.quote(PREFIX+name,safe=""),headers=headers,timeout=60)
    for receipt in read("restaged-inputs858.json")["receipts"]:
        if receipt["name"] in {PREFIX+n for n in ("inputs/index.json","inputs/items/858.json","inputs/wave-000858.xz","control/480.json","control/300.json")}:
            response=get(receipt["name"][len(PREFIX):]);response.raise_for_status()
            assert response.json()["generation"]==receipt["generation"]
    for name in ("continuation-6-claim.json","claims/wave-000858.json","children/858.json",f"epochs/{state['epoch']}/claim.json"):
        assert get(name).status_code==404
    with (B.parent/"data/budget.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger=json.loads(B.read_text());entry=ledger["reservations"]["fds-tree51-nov06-continuation"]
        assert entry["state"]=="submitted" and ledger["reservations"]["fds-tree51-training"]["allowance_usd"]==20
        assert state["limit"]<=round(entry["compute_limit_usd"]*1e6)
        assert ledger["estimated_spend_usd"]+entry["allowance_usd"]<=entry["spending_ceiling"]==180
        payload=dict(state=state,restored_inputs_from=858,predecessor=read("resume5-execution.json")["name"])
        contents=json.dumps(payload).encode()
        response=requests.post("https://storage.googleapis.com/upload/storage/v1/b/"+BUCKET+"/o",params=dict(uploadType="media",name=PREFIX+"control/continuation-6.json",ifGenerationMatch=0),headers=headers,data=contents,timeout=60)
        response.raise_for_status()
        check=requests.get(url+requests.utils.quote(PREFIX+"control/continuation-6.json",safe=""),params=dict(alt="media",generation=response.json()["generation"]),headers=headers,timeout=60)
        check.raise_for_status();assert check.content==contents
        save("resume6-state.json",payload)
        with (P/"resume6-submission-intent.json").open("x") as intent:
            json.dump(dict(time=time.time(),cursor=858,workflow=WF+"-resume6"),intent)
        e=gc("workflows","execute",WF+"-resume6","--location=us-central1","--data={}")
        save("resume6-execution.json",e)
        entry.setdefault("continuations",[]).append(e["name"])
        tmp=B.with_suffix(".resume6.tmp");tmp.write_text(json.dumps(ledger,indent=2)+"\n");tmp.replace(B)
    f=R/"continuation-record07.json";record=json.loads(f.read_text())
    record["pre_storage_expiry"]=record["latest_continuation"]
    record["latest_continuation"]=dict(workflow=WF+"-resume6",execution=e["name"].split("/")[-1],created_at=e["startTime"],first_index=858,remaining_never_submitted=673,local_admission_gate=False)
    f.write_text(json.dumps(record,indent=2)+"\n")
    print("Submitted unique continuation at 858",flush=True)
    return True


if __name__=="__main__":
    with (P/"resume6-watch.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for _ in range(375):
            if settle():
                break
            print("Waiting for independent jobs to drain",flush=True)
            time.sleep(30)
        else:
            raise TimeoutError("Drain watch expired")
