"""Show the structure of ~/.hf_token_backup without revealing the token.

Reports line count, key names, value lengths and prefixes, and any whitespace or
quoting -- enough to see whether the edit came out right, without echoing the
secret into the transcript.
"""
import os, re

P = os.path.expanduser("~/.hf_token_backup")
raw = open(P, "rb").read()
print("bytes: %d  lines: %d  CR present: %s"
      % (len(raw), len(raw.split(b"\n")), b"\r" in raw))
print("smart quotes present: %s"
      % (b"\xe2\x80\x98" in raw or b"\xe2\x80\x9c" in raw))
print("---")
for i, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
    if not line.strip():
        print("%d: (blank)" % i)
        continue
    if "=" not in line:
        print("%d: NO '=' -> %r" % (i, line[:30]))
        continue
    k, v = line.split("=", 1)
    flags = []
    if v != v.strip():
        flags.append("WHITESPACE")
    if re.search(r"[\"'\u2018\u2019\u201c\u201d]", v):
        flags.append("QUOTE")
    if not v.isascii():
        flags.append("NON-ASCII")
    print("%d: key=%-20r value_len=%d value_head=%r %s"
          % (i, k.strip(), len(v), v[:4], " ".join(flags) or "clean"))
