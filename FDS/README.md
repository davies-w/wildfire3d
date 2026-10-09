# FDS — the engine and the working area

**Not committed.** See the repository `.gitignore`. FDS is a large
third-party source tree plus build output, plus gigabytes of case data, so it
is checked out and run *here* rather than vendored. Only this README is
tracked, so the layout stays documented while the contents stay out of git.

```
FDS/
  src/          checkout of firemodels/fds at the release tag in use
  src/Build/    compile output; the native arm64 binary lands here
  install/      the NIST binary distribution (fds + smokeview)
  cases/        one directory per case: deck, solver output, renders
  runs/         small ad-hoc runs and probes
  bin/          smv_quiet -- the focus-stealing fix (docs/focus-fix.md)
  apps/         SmokeviewAgent.app, kept for reference
  hf_dvc_mirror/ local DVC mirror; the authoritative copy is the HF bucket
```

`install/` is also reachable as `install/../FDS-6.11.1_SMV-6.11.2_osx` via a
symlink, because older notes refer to the distribution's own directory name.

## Setting it up

```
python3 scripts/setup_engine.py            # source checkout
python3 scripts/setup_engine.py --dist     # + the NIST binaries
python3 scripts/setup_engine.py --build    # + a native arm64 build
python3 scripts/setup_env.py               # the Python venv (numpy, dvc, ...)
```

The last one matters: the analysis venv lives at the **repo root** (`.venv`),
not in here. Anything inside `FDS/` is gitignored, so a venv in here could not
be reproduced from a clone.

On Apple Silicon the native arm64 build is worth **1.60×** over the x86-64
distribution under Rosetta, and `OMP_NUM_THREADS=4` is the optimum — 8 threads
is slower than 1. Both are established in `docs/performance.md`; don't
re-derive them.

## Paths in scripts

Rule 1 of `AGENTS.md`: no script may hardcode a location inside this
directory. Everything resolves through `paths.py` at the repo root, which
defaults `FDS_ROOT` to `FDS/` and honours `WILDFIRE3D_FDS`:

```
python3 scripts/check_no_hardcoded_paths.py          # lint; exits non-zero on offenders
WILDFIRE3D_FDS=/somewhere/else python3 <script>.py   # run against another checkout
```

Scripts find `paths.py` by walking up from their own file, so they work from
any directory and any depth without `sys.path` guesswork.
