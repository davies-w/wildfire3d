"""Set up DVC and ingest the first evidence bundle.

Storage design (see docs/storage.md): push to a local mirror directory, then
sync that to the HF bucket with the `hf` CLI; pull straight from the anonymous
HTTPS resolve URL.  So the DEFAULT remote is the read-only HTTPS one -- plain
`dvc pull` works for anyone -- and `mirror` is the push target.

Only the *evidence* is tracked, not the raw volume: .bf (wall temperature,
burning rate), .prt5 (firebrands) and .sf (slices).  ~5 MB for the headline
case against ~140 MB if the .s3d volume came too. See docs/storage.md.
"""
import os, shutil, subprocess

V = os.path.expanduser("~/FDS/.venv/bin")
DVC = os.path.join(V, "dvc")
HF = os.path.join(V, "hf")
TOKEN = open(os.path.expanduser("~/.cache/huggingface/token")).read().strip()

REPO = os.path.expanduser("~/pi/wildfire3d")
SRC = os.path.expanduser("~/FDS/cases/wick3")
MIRROR = os.path.expanduser("~/FDS/hf_dvc_mirror")
PREFIX = "wildfire3d"
BASE = "https://huggingface.co/buckets/wdavies/dvc_storage/resolve"
env = dict(os.environ, HF_TOKEN=TOKEN)


def run(cmd, cwd=REPO, show=True):
    p = subprocess.run(cmd, cwd=cwd, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if show:
        print("$ %s\n  -> %s" % (" ".join(cmd), (p.stdout or "").strip()[-250:].replace("\n", " | ")))
    return p


# 1. evidence into the experiment directory
raw = os.path.join(REPO, "experiments/07_wick3_house_ignition/raw")
os.makedirs(raw, exist_ok=True)
for f in ("wick3c_1_1.bf", "wick3c_1_2.bf", "wick3c_1.prt5",
          "wick3c_1_1.sf", "wick3c_1_2.sf"):
    src = os.path.join(SRC, f)
    if os.path.exists(src):
        shutil.copy2(src, raw)
print("evidence files:", sorted(os.listdir(raw)))

# 2. remotes
os.makedirs(MIRROR, exist_ok=True)
run([DVC, "init"] + (["-f"] if not os.path.isdir(os.path.join(REPO, ".dvc")) else []))
run([DVC, "remote", "add", "mirror", MIRROR])
run([DVC, "remote", "add", "-d", "hfhttp", "%s/%s" % (BASE, PREFIX)])

# 3. track, push to mirror, mirror up to the bucket
run([DVC, "add", "experiments/07_wick3_house_ignition/raw"])
run([DVC, "push", "-r", "mirror"])
run([HF, "buckets", "sync", MIRROR, "hf://buckets/wdavies/dvc_storage/%s" % PREFIX])
print("\ndone")
