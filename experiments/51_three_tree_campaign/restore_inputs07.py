"""Restage reviewed bytes for untouched cases after trial-bucket lifecycle deletion."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
import threading

import requests

from cloud07 import BUCKET, G, P, PREFIX, R, save


def restore():
    first = 858
    inventory = json.loads((P / "objects.json").read_text())
    assert not any(v["name"].startswith(PREFIX+"claims/wave-") and int(v["name"].split("-")[-1].split(".")[0])>=first for v in inventory)
    prior = {v["name"]:v for v in json.loads((P/"input-uploads.json").read_text())}
    hashes = json.loads((P/"package.json").read_text())["files"]
    archive = {v["name"]:v for v in json.loads((P/"terminal-retention07.json").read_text())["objects"]}
    planned = {}
    for interval in (480,300):
        name = f"control/{interval}.json"
        data = json.dumps(dict(checkpoint_seconds=interval,run_id="t51r07"),separators=(",",":")).encode()
        assert hashlib.sha256(data).hexdigest() == archive[PREFIX+name]["sha256"]
        planned[name] = data
    paths = ["inputs/index.json"]
    for i in range(first,1531):
        paths.extend([f"inputs/items/{i}.json",f"inputs/wave-{i:06d}.xz"])
    for path in paths:
        data = (R/"data/cloud07"/path).read_bytes()
        assert hashlib.sha256(data).hexdigest()==hashes[path]
        assert base64.b64encode(hashlib.md5(data).digest()).decode()==prior[PREFIX+path]["md5Hash"]
        planned[path] = data
    assert sum(map(len,planned.values())) < 120_000_000
    headers={"Authorization":"Bearer "+subprocess.check_output([G,"auth","print-access-token"],text=True).strip()}
    local=threading.local()
    def write(item):
        if not hasattr(local,"session"):
            local.session=requests.Session()
        name,data=item
        url=f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/"+requests.utils.quote(PREFIX+name,safe="")
        resp=local.session.get(url,headers=headers,timeout=60)
        if resp.status_code==404:
            resp=local.session.post(f"https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o",params={"uploadType":"media","name":PREFIX+name,"ifGenerationMatch":0},headers={**headers,"Content-Type":"application/json" if name.endswith(".json") else "application/octet-stream"},data=data,timeout=90)
        resp.raise_for_status()
        meta=resp.json()
        assert meta["md5Hash"]==base64.b64encode(hashlib.md5(data).digest()).decode() and int(meta["size"])==len(data)
        return dict(name=meta["name"],generation=meta["generation"],md5=meta["md5Hash"])
    # Restore checkpoint controls first for any independently draining workers.
    results=[write((name,planned.pop(name))) for name in ("control/480.json","control/300.json")]
    with ThreadPoolExecutor(12) as pool:
        results.extend(pool.map(write,planned.items()))
    save("restaged-inputs858.json",dict(passed=True,first_index=first,receipts=results))
    print("Restored or verified",len(results),"exact objects")


if __name__=="__main__":
    restore()
