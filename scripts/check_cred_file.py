"""Report the shape of ~/.hf_s3_cred without printing the secret.

The value of this is in what it does NOT show.  It reports line count, key
names, value lengths and whether values contain characters that would break
authentication -- quotes, spaces, carriage returns, smart quotes -- which is
where a copy-paste through an editor usually goes wrong.
"""
import os, re

PATH = os.path.expanduser("~/.hf_s3_cred")
raw = open(PATH, "rb").read()
print("bytes: %d   lines(split on \\n): %d" % (len(raw), len(raw.split(b"\n"))))
print("has CR (\\r): %s" % (b"\r" in raw))
print("has smart quote bytes (e2 80 98/9c): %s" % (b"\xe2\x80\x98" in raw or b"\xe2\x80\x9c" in raw))

for i, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
    line = line.rstrip()
    if not line:
        print("%2d: (blank)" % i)
        continue
    if "=" not in line:
        print("%2d: NO '=' -- %r" % (i, line[:40]))
        continue
    k, v = line.split("=", 1)
    flags = []
    if v != v.strip():
        flags.append("WHITESPACE")
    if re.search(r"[\"'\u2018\u2019\u201c\u201d]", v):
        flags.append("QUOTE")
    if not v.isascii():
        flags.append("NON-ASCII")
    print("%2d: %-26s len=%3d  head=%r  %s"
          % (i, k.strip(), len(v), v[:5], " ".join(flags) or "clean"))
