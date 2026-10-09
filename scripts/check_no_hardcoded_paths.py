"""Fail if any script hardcodes a working-area path.

Rule 1 of AGENTS.md: the engine root must be a parameter, not a literal, so
the tree can be relocated or built elsewhere. This is the guard that keeps
that true -- run it after adding or editing scripts.

    python3 scripts/check_no_hardcoded_paths.py

Exits non-zero and lists offenders. Quoted literals only; a path mentioned in
a docstring or comment is prose, not a dependency.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A quoted path that reaches into the working area, or an expanduser on one.
BAD = [
    re.compile(r'["\'](?:~|/Users/[^"\']*)/FDS[/"\']'),
    re.compile(r'expanduser\(\s*["\']~/FDS'),
]

SKIP_DIRS = {".git", ".venv", "FDS", ".dvc", "__pycache__", "node_modules"}

bad = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for f in fn:
        if not f.endswith(".py"):
            continue
        path = os.path.join(dp, f)
        if os.path.abspath(path) == os.path.abspath(__file__):
            continue
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            # ignore comment-only lines
            if line.lstrip().startswith("#"):
                continue
            if any(p.search(line) for p in BAD):
                bad.append("%s:%d: %s" % (os.path.relpath(path, ROOT), i, line.strip()))

if bad:
    print("hardcoded working-area paths found:\n")
    print("\n".join("  " + b for b in bad))
    print("\nUse FDS_ROOT from paths.py (see WILDFIRE3D_FDS in FDS/README.md).")
    sys.exit(1)

print("no hardcoded working-area paths in scripts")
