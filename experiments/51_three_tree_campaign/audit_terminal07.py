"""Audit retained generations using immutable upload evidence and bounded direct reads."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import threading
from urllib.parse import quote

import requests

from cloud07 import BUCKET, P, PREFIX, R, gc, save, G
import subprocess


def load(name):
    return json.loads((P / name).read_text())


def inventory():
    status = load("status.json")
    assert status["controller"]["state"] == "SUCCEEDED" and not status["jobs"] and not status["vms"]
    state = json.loads(status["controller"]["result"])["state"]
    assert not state["active"] and state["spent"] + state["reserve"] > state["limit"]
    assert load("resume3-drained-review.json")["passed"]
    objects = {item["name"]: item for item in load("objects.json")}
    assert objects and all(name.startswith(PREFIX) for name in objects)
    return objects


sessions = threading.local()
token_lock = threading.Lock()
token = None


def read_object(item):
    global token
    if not hasattr(sessions, "http"):
        sessions.http = requests.Session()
    for attempt in range(4):
        with token_lock:
            if token is None:
                token = subprocess.check_output([G, "auth", "print-access-token"], text=True).strip()
            current = token
        try:
            response = sessions.http.get(
                f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/" + quote(item["name"], safe=""),
                params={"alt": "media", "generation": item["generation"]},
                headers={"Authorization": "Bearer " + current}, timeout=90)
            if response.status_code == 401:
                with token_lock:
                    if current == token:
                        token = None
            response.raise_for_status()
            data = response.content
            assert len(data) == int(item["size"])
            assert base64.b64encode(hashlib.md5(data).digest()).decode() == item["md5Hash"]
            return data
        except requests.RequestException:
            if attempt == 3:
                raise


def audit():
    objects = inventory()
    cache = {record["name"]: record for record in load("worker-proofs.json")}
    parts = {}
    receipts = P / "terminal-small-hashes"
    receipts.mkdir(exist_ok=True)
    manifests = [item for name, item in objects.items() if name.endswith("/archive-manifest.json")]
    small = [item for name, item in objects.items() if not name.endswith(".tar.gz.part")]
    assert sum(int(item["size"]) for item in small) < 150_000_000

    def read_manifest(item):
        manifest = json.loads(read_object(item))
        assert manifest["complete"] and sum(p["bytes"] for p in manifest["parts"]) == manifest["bytes"]
        records = {}
        for i, part in enumerate(manifest["parts"]):
            assert part["name"] == f"archive-{i:05d}.tar.gz.part"
            name = item["name"].rsplit("/", 1)[0] + "/" + part["name"]
            remote = objects[name]
            assert remote["timeCreated"] <= item["timeCreated"] and int(remote["size"]) == part["bytes"]
            assert re.fullmatch("[a-f0-9]{64}", part["sha256"]) and remote["md5Hash"]
            records[name] = part["sha256"]
        return records

    with ThreadPoolExecutor(16) as pool:
        for records in pool.map(read_manifest, manifests):
            assert parts.keys().isdisjoint(records)
            parts.update(records)
    missing = [i for n, i in objects.items() if n.endswith(".tar.gz.part") and n not in parts]
    assert sum(int(i["size"]) for i in missing) < 2_000_000_000, "Review unmanifested bytes before any transfer"
    def verify(item):
        name = item["name"]
        record = dict(name=name, generation=item["generation"], md5=item["md5Hash"], bytes=int(item["size"]))
        if name in parts:
            return dict(record, sha256=parts[name], method="immutable upload MD5 and pinned writer SHA manifest")
        if name in cache:
            old = cache[name]
            assert old["md5"] == record["md5"] and old["generation"] == record["generation"]
            return dict(record, sha256=old["sha256"], method="pinned inspector read")
        path = receipts / (hashlib.sha256(name.encode()).hexdigest() + ".json")
        if path.exists():
            old = json.loads(path.read_text())
            assert all(old[k] == v for k, v in record.items())
            return old
        result = dict(record, sha256=hashlib.sha256(read_object(item)).hexdigest(), method="generation read")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(result))
        tmp.replace(path)
        return result
    with ThreadPoolExecutor(20) as pool:
        rows = list(pool.map(verify, objects.values()))
    assert len(rows) == len(objects)
    save("terminal-retention07.json", dict(passed=True, objects=rows, manifest_parts=len(parts),
         direct_read_upper_bytes=sum(int(i["size"]) for i in small + missing),
         storage="Private original generations retained. Manifest-backed parts were not downloaded again."))


if __name__ == "__main__":
    audit()
