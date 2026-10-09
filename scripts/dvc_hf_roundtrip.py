"""End-to-end proof: DVC push to a local dir, mirror to HF, pull back over HTTPS.

The design under test is asymmetric on purpose.  DVC's http:// remote is
read-only, which is exactly what a public archive wants; writes go out through
`hf buckets sync` with the token.  So:

  1. build a test dataset, dvc add it
  2. dvc push to a LOCAL directory remote
  3. hf buckets sync that directory into the bucket
  4. throw away the cache and the data
  5. dvc pull from the anonymous HTTPS remote
  6. verify the bytes came back identical

Step 6 is the one that matters -- a silent empty pull would otherwise look like
success, which is how these things usually fool you.
"""
import hashlib, os, shutil, subprocess, sys

V = os.path.expanduser("~/FDS/.venv/bin")
HF = os.path.join(V, "hf")
DVC = os.path.join(V, "dvc")
TOKEN = open(os.path.expanduser("~/.cache/huggingface/token")).read().strip()

WORK = os.path.expanduser("~/FDS/hf_dvc_test")
MIRROR = os.path.expanduser("~/FDS/hf_dvc_mirror")
PREFIX = "dvc_test"
BASE = "https://huggingface.co/buckets/wdavies/dvc_storage/resolve"
env = dict(os.environ, HF_TOKEN=TOKEN)


def run(cmd, cwd=None, show=True):
    p = subprocess.run(cmd, cwd=cwd, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if show:
        print("$ %s\n  -> exit %d %s" % (" ".join(cmd), p.returncode,
                                         (p.stdout or "").strip()[-260:].replace("\n", " | ")))
    return p


# 1. fresh workspace with a dataset
shutil.rmtree(WORK, ignore_errors=True)
shutil.rmtree(MIRROR, ignore_errors=True)
os.makedirs(WORK)
os.makedirs(MIRROR)
data = os.path.join(WORK, "data.bin")
blob = os.urandom(2_000_000)
open(data, "wb").write(blob)
want = hashlib.md5(blob).hexdigest()
run([DVC, "init", "--no-scm"], cwd=WORK)
run([DVC, "remote", "add", "-d", "mirror", MIRROR], cwd=WORK)
run([DVC, "add", "data.bin"], cwd=WORK)

# 2 + 3. push locally, then mirror the cache up to the bucket
print(run([DVC, "push"], cwd=WORK).stdout.strip()[-200:])
print(run([HF, "buckets", "sync", MIRROR,
           "hf://buckets/wdavies/dvc_storage/%s" % PREFIX]).stdout.strip()[-300:])

# 4. destroy the local copy of both data and cache
os.remove(data)
shutil.rmtree(os.path.join(WORK, ".dvc", "cache"))
run([DVC, "status"], cwd=WORK)

# 5. pull from the anonymous HTTPS remote
run([DVC, "remote", "add", "hfhttp", "%s/%s" % (BASE, PREFIX)], cwd=WORK)
run([DVC, "pull", "-r", "hfhttp"], cwd=WORK)

# 6. verify
if not os.path.exists(data):
    sys.exit("FAIL: data.bin was not restored")
got = hashlib.md5(open(data, "rb").read()).hexdigest()
print("\nwant md5 %s\ngot  md5 %s" % (want, got))
print("RESULT:", "PASS" if got == want else "FAIL")
