"""Rebuild ~/.hf_token_backup from the canonical token, with an honest label.

The earlier sed edit was clobbered: TextEdit still had the file open from when
it was created for pasting, and saved its stale buffer back over the change.
This takes the token from ~/.cache/huggingface/token -- the copy the `hf` CLI
actually uses -- and writes the backup fresh as a single labelled line.

Writes atomically (temp file + rename) so a concurrent editor cannot leave a
half-written credential behind.
"""
import os, tempfile

SRC = os.path.expanduser("~/.cache/huggingface/token")
DEST = os.path.expanduser("~/.hf_token_backup")

token = open(SRC).read().strip()
if not token.startswith("hf_"):
    raise SystemExit("refusing: %s does not look like an HF token" % SRC)

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(DEST))
with os.fdopen(fd, "w") as fh:
    fh.write("HF_BUCKET_TOKEN=%s\n" % token)
os.chmod(tmp, 0o600)
os.replace(tmp, DEST)

raw = open(DEST, "rb").read()
print("wrote %s  bytes=%d  mode=%o" % (DEST, len(raw), os.stat(DEST).st_mode & 0o777))
for line in raw.decode().splitlines():
    k, _, v = line.partition("=")
    print("  key=%-18r value_len=%d value_head=%r" % (k, len(v), v[:4]))
