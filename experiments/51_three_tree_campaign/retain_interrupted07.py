"""Keep a bounded private copy of the newest surviving checkpoint per interrupted case."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import threading

import requests

from cloud07 import BUCKET, G, P, PREFIX


def main():
    root = P / "interruption-backups"
    root.mkdir(mode=0o700, exist_ok=True)
    inventory = {v["name"]: v for v in json.loads((P/"objects.json").read_text())}
    known = set(json.loads((P/"progress-summary.json").read_text())["confirmed_spot_interruptions"])
    known.update(x["wave"] for x in json.loads((P/"terminal-interruption-inventory.json").read_text())["cases"])
    known.add("wave-000824")
    proofs = json.loads((P/"worker-proofs.json").read_text())
    for x in proofs:
        if x["name"].endswith("/failed-task.json"):
            known.add(x["name"].split("/")[-2])
    index = {wave:[] for wave in sorted(known)}
    for x in inventory.values():
        n = x["name"][len(PREFIX):]
        w = n.split("/")[0]
        if w in index and n.endswith("/verified.json") and "/checkpoints/" in n:
            index[w].append(x["name"].rsplit("/",1)[0]+"/")
    chosen = {}
    for wave, prefixes in index.items():
        for prefix in sorted(prefixes,reverse=True):
            members = [v for n,v in inventory.items() if n.startswith(prefix)]
            if any(v["name"]==prefix+"archive-manifest.json" for v in members):
                chosen[wave] = members
                break
    assert sum(int(x["size"]) for group in chosen.values() for x in group) < 4_000_000_000
    token = subprocess.check_output([G,"auth","print-access-token"],text=True).strip()
    sessions = threading.local()
    def preserve(pair):
        wave, members = pair
        saved = {}
        for v in members:
            rel = v["name"][len(PREFIX):]
            assert ".." not in rel.split("/") and rel.startswith(wave+"/")
            file = root/rel
            file.parent.mkdir(parents=True, exist_ok=True)
            if file.exists():
                data=file.read_bytes()
            else:
                if not hasattr(sessions,"http"):
                    sessions.http=requests.Session()
                response=sessions.http.get(v["mediaLink"],headers={"Authorization":"Bearer "+token},timeout=150)
                if response.status_code==404:
                    return dict(wave=wave,passed=False,reason="generation no longer available")
                response.raise_for_status()
                data=response.content
            assert len(data)==int(v["size"]) and base64.b64encode(hashlib.md5(data).digest()).decode()==v["md5Hash"]
            if not file.exists():
                tmp=file.with_suffix(".download")
                tmp.write_bytes(data)
                os.replace(tmp,file)
            saved[file.name]=dict(generation=v["generation"],sha256=hashlib.sha256(data).hexdigest())
        manifest=json.loads((file.parent/"archive-manifest.json").read_text())
        assert manifest["complete"]
        for part in manifest["parts"]:
            if part["name"] not in saved:
                return dict(wave=wave,passed=False,reason="missing archive part")
            assert saved[part["name"]]["sha256"]==part["sha256"]
        return dict(wave=wave,passed=True,files=saved)
    with ThreadPoolExecutor(6) as pool:
        results=list(pool.map(preserve,chosen.items()))
    report=dict(results=results,not_observed=sorted(known-chosen.keys()))
    tmp=root/"inventory.tmp";tmp.write_text(json.dumps(report,indent=2));tmp.replace(root/"inventory.json")
    print("Complete private checkpoint copies:",sum(v["passed"] for v in results),"of",len(known),"reviewed interruptions",flush=True)


if __name__=="__main__":
    main()
