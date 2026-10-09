# Working rules for this repository

## Layout

```
docs/          the findings
experiments/   one directory per experiment, self-contained
scripts/       shared tooling used by more than one experiment
```

There is a **working area outside the repo** at `~/FDS`: the FDS install,
`~/FDS/cases/<case>/`, and the raw solver output. That directory is data, not
source control. Nothing here may depend on a path inside it except when reading
raw output, and then the path must be a parameter, not a literal.

## Rules

**1. Tooling belongs in this repository, not in the working area.**

Any script that produces, checks or explains a result goes in the repo — under
`experiments/<name>/` if it supports one experiment, under `scripts/` if it is
shared. Do **not** leave scripts loose in `~/FDS`. That is how this project
ended up with 88 unversioned scripts, several of which contradicted each other.

A diagnostic is not scratch. A script that proves a result is trustworthy is
part of the result, and belongs beside it.

**2. Every claim must be traceable to data.**

Rendered images are *not* evidence. A colour in a frame comes from the
renderer, and the renderer can be wrong — that has already happened here: a
two-pass blend showed a tree as unburned while the boundary data had its
burning rate pinned at the colour-bar maximum.

Before a claim goes in a README, read the number out of the boundary or slice
data with `fds2ascii`. State which surface, which quantity, and which time.

**3. Every experiment directory stands alone.**

Its `.fds`, the scripts that ran and analysed it, its `README.md` and its
results. A reader should be able to take one directory and reproduce that
result without reading anything else.

Each README states the aim, the numbers, and the conclusion — including
negative results, which here have been the most informative.

**4. Every experiment is a DVC pipeline, and raw output is never git.**

Each experiment carries a `dvc.yaml`. Its stages are that experiment's run
order and nothing else — solve, strip terrain, read the boundary data, render,
validate, and stitch where there is a pair — so `dvc repro` reproduces the whole
experiment and no step is manual. `dvc.lock` **is committed**: it records the
hash of every dependency and output, which is what makes a result checkable.

- **Do not use `dvc add`.** A `.dvc` file snapshots a directory and cannot
  re-run anything. It records *that* evidence exists, not *what produced it*.
- **Adopting existing output uses `dvc commit`**, which records what is already
  on disk without running the stage. That is how an older experiment joins the
  pipeline without re-solving.
- **Outs are tracked where FDS writes them**, in `FDS/cases/<case>/`. That tree
  is gitignored, which does not affect DVC.
- Push and pull are in `docs/storage.md`. Keep the evidence (`.bf`, `.prt5`,
  `.sf`); **never** store `.restart` (88 MB each, worthless once a solve
  completes); keep `.s3d` only if you will re-render.

Content-addressed storage means adopting existing output needs no re-upload:
identical bytes keep the same hash and the blobs already in the bucket stand.

**5. Environment and performance.**

`OMP_NUM_THREADS=4`, not 8 — on this hardware 8 is slower than 1. Use the native
arm64 build. Both are established in `docs/performance.md`; don't re-derive them.

**6. Solver vs renderer.**

FDS writes files; Smokeview decides pixels. When something looks wrong, decide
which program owns the behaviour before debugging. Re-rendering never needs a
re-solve and vice versa.

## When something is uncertain

Say so. "I have not proven this" is a useful sentence. Do not present a
plausible guess as a finding — the cost of a retraction here has already been
measured in hours.
