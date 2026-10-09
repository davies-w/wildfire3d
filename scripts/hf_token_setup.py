"""Install the HF token where the `hf` CLI looks for it, then verify bucket access.

The token lives in `~/.hf_token_backup` as a single labelled line:

    HF_BUCKET_TOKEN=hf_...

This copies it to `~/.cache/huggingface/token`, the location the CLI reads
automatically, with 0600 permissions, and then checks the bucket is reachable
and still public -- visibility matters, because a private bucket would break
anonymous `dvc pull` for everyone else.

Usage:  python3 hf_token_setup.py [/path/to/hf] [/path/to/repo/venv]
"""
import os, subprocess, sys

SRC = os.path.expanduser("~/.hf_token_backup")
TOKENPATH = os.path.expanduser("~/.cache/huggingface/token")
BUCKET = "wdavies/dvc_storage"
KEY = "HF_BUCKET_TOKEN"

hf_bin = sys.argv[1] if len(sys.argv) > 1 else "hf"

# read the labelled line; refuse anything that is not an HF token
token = None
if os.path.exists(SRC):
    for line in open(SRC):
        k, _, v = line.strip().partition("=")
        if k.strip() == KEY:
            token = v.strip().strip('"').strip("'")
if not token:
    sys.exit("no %s=... line found in %s" % (KEY, SRC))
if not token.startswith("hf_"):
    sys.exit("refusing: %s does not look like an HF token" % KEY)

os.makedirs(os.path.dirname(TOKENPATH), exist_ok=True)
open(TOKENPATH, "w").write(token)
os.chmod(TOKENPATH, 0o600)
print("installed %s -> %s (%d chars, mode 600)" % (SRC, TOKENPATH, len(token)))

env = dict(os.environ, HF_TOKEN=token)
for args in (["buckets", "list"], ["buckets", "info", BUCKET]):
    print("\n$ hf " + " ".join(args))
    p = subprocess.run([hf_bin] + args, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(p.stdout.strip()[-400:])
