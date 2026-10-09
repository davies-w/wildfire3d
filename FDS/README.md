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
python3 scripts/setup_engine.py --deps --build   # everything, from scratch
python3 scripts/setup_env.py                     # the Python venv (numpy, dvc, ...)
```

`--deps --build` is the whole chain and is safe to re-run: it checks the Xcode
Command Line Tools, installs Homebrew if there is none, installs the
prerequisites declared in the repository `Brewfile` (`brew bundle`), clones the
FDS source at its release tag, clones HYPRE and SUNDIALS at the tags
`src/fds/Build/makefile` asks for, builds those two, builds the engine with
`HYPRE_HOME` and `SUNDIALS_HOME` exported, and verifies the result is arm64 and
contains HYPRE. It is idempotent: a second run skips everything in about three
seconds.

Every step fails loudly. That matters here: the engine without HYPRE builds
cleanly, reports success, and then cannot run any case where FDS selects the
UGLMAT pressure solver — which is experiments 01, 03 and part of 08. Build it
this way, not by hand.

`--root DIR` builds into `DIR` instead of `FDS/`, which is how the
from-scratch path is tested without touching a working checkout.

The standard `--dist` fetches the NIST binary distribution, which is where
Smokeview comes from and is needed for rendering.

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
