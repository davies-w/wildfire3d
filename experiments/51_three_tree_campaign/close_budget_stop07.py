"""Close the drained third continuation after science, retention and allocation checks."""
import json
import math
import fcntl
from cloud07 import B, BUCKET, P, PREFIX, PROJECT, R, RESERVATION, gc, save, sha


def read(name):
    return json.loads((P / name).read_text())


def verify_science():
    covered = set()
    for selection in P.glob("collection-group*.json"):
        group = selection.stem.split("-")[-1]
        receipt = read("preservation-" + group + ".json")
        plan = P / ("scientific-plan-" + group + ".json")
        assert receipt["passed"] and receipt["remote_size_and_xet_verified"] and receipt["directory_anonymous_readback"]
        assert receipt["plan_sha256"] == sha(plan)
        indices = set(json.loads(selection.read_text())["indices"])
        assert not indices.intersection(covered)
        covered.update(indices)
    verified = set()
    for path in (R / "data/completed07").glob("wave-*/proof.json"):
        proof = json.loads(path.read_text())
        assert proof["passed"] and len(proof["cases"]) == 1
        case = proof["cases"][0]
        assert case["passed"] and case["archive_parts_verified"] and case["physical_time_s"] >= 180 - 1e-5
        verified.add(int(path.parent.name.split("-")[1]))
    assert verified == covered and len(verified) + 468 == read("progress-summary.json")["verified_complete"] == 1022
    claims = {i for i in range(586)}
    excluded = {int(x.split("-")[1]) for x in read("progress-summary.json")["confirmed_spot_interruptions"]}
    assert len(excluded) == 27 and verified == claims - excluded - {9, 15, 276, 514, 515}


def empty_resources():
    result = {}
    for name, args in [("jobs", ("batch", "jobs", "list", "--location=us-central1")),
                       ("vms", ("compute", "instances", "list")), ("disks", ("compute", "disks", "list"))]:
        result[name] = gc(*args, "--filter=name~t51r07")
        assert not result[name]
    return result


def retire():
    rules = [("bucket", "fds-worker", "roles/storage.objectViewer", "read-condition.json", "tree51-campaign07-read"),
             ("bucket", "fds-watchdog", "roles/storage.objectViewer", "controller-read-condition.json", "tree51-campaign07-controller-read"),
             ("project", "fds-watchdog", "projects/"+PROJECT+"/roles/fdsTree51TaskReader", "task-read-condition.json", "tree51-task-read07"),
             ("project", "fds-watchdog", "projects/"+PROJECT+"/roles/fdsTree51WaveRunner", "execution-run-condition.json", "tree51-campaign07-execution-run")]
    for scope, account, role, file, title in rules:
        condition = read(file)
        assert condition["title"] == title
        member = "serviceAccount:"+account+"@"+PROJECT+".iam.gserviceaccount.com"
        command, target = (("storage", "buckets"), "gs://"+BUCKET) if scope=="bucket" else (("projects",), PROJECT)
        def bindings():
            return [b for b in gc(*command, "get-iam-policy", target).get("bindings", [])
                    if b.get("condition", {}).get("title") == title]
        existing = bindings()
        if existing:
            assert len(existing)==1 and existing[0]["condition"]==condition and existing[0]["role"]==role
            assert existing[0]["members"]==[member]
            gc(*command, "remove-iam-policy-binding", target, "--member="+member, "--role="+role,
               "--condition-from-file="+str(P/file))
        assert not bindings()
    save("grants-retired.json", dict(passed=True, exact_titles=[r[-1] for r in rules], independent_readback=True))


def close():
    assert not (P/"closed.json").exists()
    verify_science()
    assert read("terminal-retention07.json")["passed"]
    state = json.loads(read("status.json")["controller"]["result"])["state"]
    assert state["cursor"]==586 and not state["active"] and state["spent"]+state["reserve"]>state["limit"]
    audit = read("resume3-drained-review.json")
    assert audit["passed"] and audit["pairs"]==583 and audit["held_indices"]==[9,15,276,514,515]
    amount = audit["compute_upper_usd"]
    holds = 5 * state["reserve"]
    assert state["limit"]-math.ceil(amount*1e6)-holds < state["reserve"]
    empty = empty_resources()
    retire()
    with (B.parent/"data/budget.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(B.read_text())
        assert ledger["authorized_usd"]==200 and ledger["reservations"]["fds-tree51-training"]["allowance_usd"]==20
        entry = ledger["reservations"][RESERVATION]
        if entry["state"]=="submitted":
            remaining = entry["allowance_usd"] - amount
            entry.update(state="budget_stop_audited_closed", original_allowance_usd=entry["allowance_usd"],
                         allowance_usd=remaining, cost=dict(usd=amount, allocation_seconds=audit["allocation_seconds"]),
                         retained_allowance_reason="Original ancillary and unresolved reservations; no solver admissions.")
            ledger["estimated_spend_usd"] += amount
            ledger["reserved_usd"] -= amount
            ledger["accounting"]["spend_estimate_usd"] = ledger["estimated_spend_usd"]
            assert ledger["estimated_spend_usd"]+ledger["reserved_usd"] <= 200
            tmp=B.with_suffix(".closing.tmp");tmp.write_text(json.dumps(ledger,indent=2)+"\n");tmp.replace(B)
        assert entry["state"]=="budget_stop_audited_closed" and entry["cost"]["usd"]==amount
        save("closed.json",dict(passed=True,reason="Insufficient compute allowance to reserve the next case",
             empty=empty,grant_readback=read("grants-retired.json"),allocation=audit,verified_complete=1022,
             retained_allowance_usd=entry["allowance_usd"],science_backups_verified=True,target_complete=False))


if __name__ == "__main__":
    close()
