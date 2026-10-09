# FDS — the engine

This directory holds the fire model itself, and is **not committed** (see the
repository `.gitignore`). The engine is a large third-party source tree plus
build output, so it is checked out and built here rather than vendored.

```
FDS/
  src/       checkout of firemodels/fds at the release tag in use
  build/     compile output (the native arm64 fds binary lands here)
  install/   the NIST binary distribution (fds + smokeview), if used
```

## Why in-repo

Keeping the engine under the project means a recorded, reproducible layout: the
version in use, the build recipe and the case data all sit together, and nothing
depends on a path somewhere else in the home directory. It also means the
engine can be rebuilt from scratch without hunting for where it was put.

## Setting it up

```
python3 scripts/setup_engine.py
```

That clones the tag and builds it. On Apple Silicon the native arm64 build is
worth **1.60×** over the x86-64 distribution running under Rosetta, and
`OMP_NUM_THREADS=4` is the optimum — 8 threads is slower than 1. Both are
established in `docs/performance.md`; don't re-derive them.

## Paths in scripts

Scripts must not hardcode a location inside this directory. Take the engine
root as a parameter or from an environment variable (`WILDFIRE3D_FDS`), as
required by rule 1 of `AGENTS.md`.
