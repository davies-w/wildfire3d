"""Measure how well FDS binary output compresses.

FDS writes raw little-endian floats with no compression.  If the volume is
mostly longs and zeros, gzip gets a lot back; if it is noise, it does not.  This
decides whether "store raw output" is cheap or not.

Samples at most 120 MB of the largest file of each suffix to keep it quick.
"""
import os, zlib

def biggest(root, ext):
    best = (0, None)
    for dp, _, fn in os.walk(root):
        for f in fn:
            if f.endswith(ext):
                p = os.path.join(dp, f)
                s = os.path.getsize(p)
                if s > best[0]:
                    best = (s, p)
    return best

ROOT = os.path.expanduser("~/FDS/cases")
CAP = 120_000_000
for ext in (".s3d", ".sf", ".prt5", ".restart", ".bf"):
    s, p = biggest(ROOT, ext)
    if not p:
        continue
    take = min(s, CAP)
    with open(p, "rb") as fh:
        data = fh.read(take)
    z = zlib.compress(data, 6)
    print("%-9s %7.1f MB sampled -> %7.1f MB gz   ratio %.2fx   (%s)"
          % (ext, take / 1e6, len(z) / 1e6, take / len(z), os.path.basename(p)))
