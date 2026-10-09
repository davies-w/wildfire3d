"""Verify anonymous pull: prove a stranger can get the data with no credentials.

The whole storage design rests on this.  Destroys the local cache and one
experiment's raw/ directory, then pulls through the HTTP remote with every HF
credential REMOVED from the environment, and compares checksums.  A silently
empty pull would otherwise look like success.

    python3 verify_anon_pull.py experiments/13_ladder_tree_pair
"""
import hashlib, os, shutil, subprocess, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import REPO, VENV_BIN  # noqa: E402

if len(sys.argv) < 2:
    sys.exit("usage: verify_anon_pull.py <experiment dir>")
RAW = os.path.abspath(os.path.join(sys.argv[1], "raw"))
if not os.path.isfile(os.path.join(os.path.dirname(RAW), "raw.dvc")):
    sys.exit("%s is not DVC-tracked (no raw.dvc beside it)" % RAW)
CACHE = os.path.join(REPO, ".dvc/cache")


def md5s(d):
    return {f: hashlib.md5(open(os.path.join(d, f), "rb").read()).hexdigest()
            for f in sorted(os.listdir(d))}


before = md5s(RAW)
print("%s: %d files, %d bytes"
      % (RAW, len(before), sum(os.path.getsize(os.path.join(RAW, f))
                               for f in before)))

# strip every HF credential from the environment
env = {k: v for k, v in os.environ.items()
       if not k.startswith(("HF_", "HUGGING", "AWS_"))}
shutil.rmtree(RAW)
shutil.rmtree(CACHE, ignore_errors=True)
print("removed raw/ and the dvc cache")

p = subprocess.run([os.path.join(VENV_BIN, "dvc"), "pull"], cwd=REPO, env=env,
                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("dvc pull (no credentials):\n  "
      + (p.stdout or "").strip()[-400:].replace("\n", "\n  "))

if not os.path.isdir(RAW):
    raise SystemExit("FAIL: nothing restored")
after = md5s(RAW)
for f in before:
    print("  %s %s" % ("ok " if after.get(f) == before[f] else "BAD", f))
print("\nRESULT:", "PASS" if before == after else "FAIL")
