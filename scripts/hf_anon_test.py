"""Can a PUBLIC HF bucket file be fetched anonymously over HTTPS?

If yes, the storage story is: push with the `hf` CLI (token), pull over plain
HTTPS with no credentials -- which satisfies even the strictest reading of
"publicly fetchable" and makes a read-only DVC http:// remote possible.

Uploads a distinctive test file with the token, then tries to fetch it with
curl and NO Authorization header, and reports the status code.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import VENV_BIN  # noqa: E402

import os, subprocess

HF = os.path.join(VENV_BIN, "hf")
TOKEN = open(os.path.expanduser("~/.cache/huggingface/token")).read().strip()
BUCKET = "wdavies/dvc_storage"
KEY = "anon_test/probe.txt"
MARKER = "hf-bucket-anonymous-probe-12345"

local = os.path.expanduser("~/hf_probe.txt")
open(local, "w").write(MARKER + "\n")

env = dict(os.environ, HF_TOKEN=TOKEN)
dst = "hf://buckets/%s/%s" % (BUCKET, KEY)
p = subprocess.run([HF, "buckets", "cp", local, dst], env=env, text=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("upload:", (p.stdout or "").strip()[-300:], "exit", p.returncode)

URL = "https://huggingface.co/buckets/%s/resolve/%s" % (BUCKET, KEY)
print("\nprobing anonymously:", URL)
c = subprocess.run(["curl", "-sS", "-o", "/tmp/probe_out.txt", "-w", "%{http_code}",
                    "-L", URL], text=True, stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
print("http status:", c.stdout.strip())
try:
    body = open("/tmp/probe_out.txt", "rb").read()
    print("got marker:", MARKER.encode() in body, " bytes:", len(body))
    print("body head:", body[:120])
except OSError as e:
    print("no body:", e)
