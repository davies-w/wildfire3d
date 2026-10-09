"""Verify anonymous pull: prove a stranger can get the data with no credentials.

The whole storage design rests on this.  Destroys the local cache and the data,
then pulls through the HTTP remote with the HF token REMOVED from the
environment, and compares checksums.  A silently empty pull would otherwise look
like success.
"""
import hashlib, os, shutil, subprocess

V = os.path.expanduser("~/FDS/.venv/bin")
DVC = os.path.join(V, "dvc")
REPO = os.path.expanduser("~/pi/wildfire3d")
RAW = os.path.join(REPO, "experiments/07_wick3_house_ignition/raw")
CACHE = os.path.join(REPO, ".dvc/cache")

before = {}
for f in sorted(os.listdir(RAW)):
    before[f] = hashlib.md5(open(os.path.join(RAW, f), "rb").read()).hexdigest()
print("tracked files: %d, %d bytes" % (len(before), sum(
    os.path.getsize(os.path.join(RAW, f)) for f in before)))

# strip every HF credential from the environment
env = {k: v for k, v in os.environ.items()
       if not k.startswith(("HF_", "HUGGING", "AWS_"))}
for k in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "AWS_ACCESS_KEY_ID",
          "AWS_SECRET_ACCESS_KEY"):
    env.pop(k, None)

shutil.rmtree(RAW)
shutil.rmtree(CACHE, ignore_errors=True)
print("removed raw/ and the dvc cache")

p = subprocess.run([DVC, "pull"], cwd=REPO, env=env, text=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print("dvc pull (no credentials):")
print("  " + (p.stdout or "").strip()[-400:].replace("\n", "\n  "))

if not os.path.isdir(RAW):
    raise SystemExit("FAIL: nothing restored")

after = {f: hashlib.md5(open(os.path.join(RAW, f), "rb").read()).hexdigest()
         for f in sorted(os.listdir(RAW))}
ok = before == after
for f in before:
    mark = "ok " if after.get(f) == before[f] else "BAD"
    print("  %s %s" % (mark, f))
print("\nRESULT:", "PASS" if ok else "FAIL")
