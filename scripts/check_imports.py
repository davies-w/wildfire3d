"""Check every third-party import in the repo is actually installed.

Written after the venv move silently dropped pypdf: requirements.txt was built
from the *direct* dependencies I happened to remember, and the PDF helper
scripts then failed.  This walks every file, extracts the modules imported,
drops the standard library and the repo's own modules, and tries to import the
rest.  Anything that fails is a missing dependency.

    .venv/bin/python scripts/check_imports.py
"""
import ast, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", ".venv", "FDS", ".dvc", "__pycache__"}

files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    files += [os.path.join(dp, f) for f in fn if f.endswith(".py")]

# modules the repo provides itself, at any depth
local = {os.path.splitext(os.path.basename(f))[0] for f in files}

mods = set()
for f in files:
    try:
        tree = ast.parse(open(f, encoding="utf-8", errors="replace").read())
    except SyntaxError as e:
        print("SYNTAX ERROR %s: %s" % (os.path.relpath(f, ROOT), e))
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])

third = sorted(m for m in mods
               if m not in sys.stdlib_module_names and m not in local)

missing = []
for m in third:
    r = subprocess.run([sys.executable, "-c", "import %s" % m],
                       capture_output=True)
    if r.returncode != 0:
        missing.append(m)
    print("  %-18s %s" % (m, "ok" if r.returncode == 0 else "MISSING"))

print("\n%d third-party imports, %d missing" % (len(third), len(missing)))
if missing:
    print("missing:", ", ".join(missing))
    sys.exit(1)
