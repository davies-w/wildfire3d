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

**4. Raw output is versioned with DVC, never git.**

Push and pull instructions are in `docs/storage.md`. Policy: keep the evidence
(`.bf`, `.prt5`, `.sf`); **never** store `.restart` (88 MB each, worthless once
a solve completes); keep `.s3d` only if you will re-render.

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
