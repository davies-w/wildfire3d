"""Confirm DVC still works after the working area moved into FDS/.

The real test is not "can I fetch a URL" but "can a fresh, credential-free
checkout get the data back". So: move the tracked output aside, scrub every
HF credential from the environment, pull from the *default* remote, and check
the restored files against the md5s DVC recorded.

Expects the DVC binary as argv[1] (kept as an argument so this does not
hardcode a virtualenv path).
"""
import json, os, shutil, subprocess, sys

DVC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments/07_wick3_house_ignition")
RAW = os.path.join(EXP, "raw")

env = {k: v for k, v in os.environ.items()
       if not k.startswith(("HF_", "HUGGING"))}
env["HOME"] = "/tmp/dvc_anon_home"          # no ~/.cache/huggingface/token
os.makedirs(env["HOME"], exist_ok=True)
env["PATH"] = os.path.dirname(DVC) + os.pathsep + env["PATH"]

if os.path.isdir(RAW):
    shutil.rmtree(RAW)

p = subprocess.run([DVC, "pull"], cwd=ROOT, env=env,
                   capture_output=True, text=True)
print(p.stdout.strip() or p.stderr.strip())

import hashlib
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

manifest = json.load(open(os.path.join(ROOT, ".dvc/cache/files/md5/16",
                                       "a96bb4dcf4fa958c3154748543affb.dir")))
bad = []
for e in manifest:
    f = os.path.join(RAW, e["relpath"])
    if not os.path.isfile(f):
        bad.append("%s missing" % e["relpath"])
    elif md5(f) != e["md5"]:
        bad.append("%s md5 mismatch" % e["relpath"])

if bad:
    print("\nFAIL:", *bad, sep="\n  ")
    sys.exit(1)
print("\nAnonymous dvc pull after the move: PASS (%d files)" % len(manifest))
