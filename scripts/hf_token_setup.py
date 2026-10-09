"""Install the HF token where the `hf` CLI looks for it, then test bucket access.

The S3 credential route is unavailable (no "Generate S3 credentials" in the
token menu), so the plan is `hf buckets sync` driven by an ordinary HF token.
The token currently sits on the AWS_SECRET_ACCESS_KEY line of ~/.hf_s3_cred
because it was pasted into the wrong slot; this lifts it out and writes it to
~/.cache/huggingface/token, which the CLI reads automatically.
"""
import os, subprocess, sys

CRED = os.path.expanduser("~/.hf_s3_cred")
TOKENPATH = os.path.expanduser("~/.cache/huggingface/token")
BUCKET = "wdavies/dvc_storage"

token = None
for line in open(CRED):
    v = line.strip().partition("=")[2].strip().strip('"').strip("'")
    if v.startswith("hf_"):
        token = v
if not token:
    sys.exit("no hf_... token found in %s" % CRED)

os.makedirs(os.path.dirname(TOKENPATH), exist_ok=True)
open(TOKENPATH, "w").write(token)
os.chmod(TOKENPATH, 0o600)
print("token installed at %s (%d chars)" % (TOKENPATH, len(token)))

HF = os.path.expanduser("~/FDS/.venv/bin/hf")
env = dict(os.environ, HF_TOKEN=token)
for args in (["buckets", "list"], ["buckets", "info", BUCKET],
             ["buckets", "list", BUCKET]):
    print("\n$ hf " + " ".join(args))
    p = subprocess.run([HF] + args, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(p.stdout.strip()[-600:])
