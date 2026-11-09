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

- **`dvc add` is for inputs, never for outputs.** A `.dvc` file snapshots a
  file and cannot re-run anything, so it must not stand in for a stage. An
  external input that nothing here produces is exactly what it is for:
  experiment 09's `ec2.json` is a 317 MB pricing dump with no stage that could
  ever make it.
- **Check before `git add` on anything binary or large.** Source, config,
  results text and rendered gifs belong in git; bulk data does not. GitHub
  rejects any single file over 100 MB outright, so such a commit is unpushable
  and undoing it needs a history rewrite. When asked to add one, say so and
  name the alternative before doing it.
- **Adopting existing output uses `dvc commit`**, which records what is already
  on disk without running the stage. That is how an older experiment joins the
  pipeline without re-solving.
- **Outs live in the experiment, under `data/`.** The experiment directory
  holds config — deck, `dvc.yaml`, `README`, one-off `scripts/` — and `data/`
  holds every solver output; `dvc.yaml` names them, and this is what makes a
  single directory reproducible on its own. Nothing is written into the engine
  tree: `FDS/` holds the engine and FDS's own working files, and nothing that
  is authored or versioned goes there.
- Push and pull are in `docs/storage.md`. Keep the evidence (`.bf`, `.prt5`,
  `.sf`); retain a bounded restart checkpoint for incomplete or interrupted solves so work can resume; remove obsolete checkpoints only after a completed solve and verified results. Keep `.s3d` only if you will re-render.

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

## Standing instruction: disclose material simplifications

Do not obscure or omit details that materially affect the user's interpretation of an experiment, visualization, or result. Disclose them proactively when proposing the experiment and when presenting results, rather than waiting for the user to discover them or ask. A generic label such as "toy example" is insufficient.

- Use accurate names and give relevant dimensions: for example, "approximately 2 m vegetation crowns beside a 4 m house block," not unqualified "trees and a house." Do not imply a species, mature-tree scale, realistic building, or validated material behavior unless the setup supports it.
- State consequential assumptions and omissions, including geometry, fuel representation, imposed ignition sources and duration, ignition criterion, mesh resolution, and whether embers are modeled. Explain how they limit the conclusion; prioritize details that change the user's understanding rather than burying them in technical output.
- Distinguish simulated physics, renderer choices, and learned model values. Explain what colours, dots, arrows, and animation stages mean; do not imply physical time or temperature for neural activations.
- State precisely what evidence establishes and what remains untested. Do not present success on a simplified scene as validation for realistic properties.
- If earlier wording concealed a material distinction, correct it plainly and update the relevant description. Do not silently substitute an easier experiment for the user's intended question.

## Standing instruction: status requests do not pause work

A user request for an update or status is a checkpoint, not a stop instruction. Answer briefly and continue the authorized experiment, monitoring, diagnosis and fixes. Keep existing spending limits and approval boundaries. Do not end ongoing work merely because the user asked a question. Stop or pause only when requested, when work is complete, or when a real blocker requires input; complete unaffected authorized work first.

## Long-running simulation recovery

Following the user's explicit request to avoid losing completed computation, future long runs must checkpoint periodically, preserve and upload the final usable checkpoint when interrupted, and support a tested resume path. Do not delete restart files from incomplete runs. Report the runtime estimate, deadline, checkpoint policy and extension limitations before launch. Existing runs without this capability must be described honestly; partial scientific outputs are not a resumable checkpoint.

## Standing authorization: repository uploads and budgeted cloud work

The user explicitly authorized uploads and Git pushes to repositories they control,
and cloud work within the existing $125 ledger allowance, without asking again
(2026-10-28). Account for existing spend, reservations and the proposed allowance
before launching work. This authorization does not increase the budget or authorize
publishing to unrelated destinations. Continue authorized work while reporting
material results and limitations.

## Standing instruction: commit, push and preserve artifacts

Always Git commit and Git push task-related code, configuration, documentation,
and DVC pointers and lockfiles before declaring work complete. Always ensure
created or updated data artifacts, including models, checkpoints and training
datasets, are DVC controlled and DVC pushed. Preserve resumable checkpoints.
Stage only relevant changes; do not sweep unrelated work into a commit.

For this repository, when the user says **“DVC push”**, use
`python scripts/dvc_hf.py push` with the reviewed artifact plan. It uploads the
original files directly to their DVC MD5 object paths in the configured public
Hugging Face bucket, verifies every remote size and Xet hash, and anonymously
reads back directory manifests. A local mirror copy is not a push.

Prefer `dvc.yaml` → `dvc.lock` for pipeline outputs. Use
`python scripts/dvc_hf.py commit path/to/dvc.yaml:stage` to adopt existing output
bytes without running the stage or making a persistent cache copy. Historical
artifacts and external/source inputs may use `.dvc` pointers through
`python scripts/dvc_hf.py track PATH...`, per the user's explicit authorization
(2026-11-01). Then push the generated plan and commit/push the metadata.
Do not run ordinary `dvc push` against the HTTP remote or recreate a local
mirror. Do not upload whole directories without a reviewed hash/object plan.
The user's public scientific-artifact authorization covers the whole project.
See `docs/storage.md` for limits and restoration checks.

Never publish budgets, financial metadata, private keys or credentials. Keep
private originals in private storage and use sanitized public exports where
necessary. These exclusions apply to Git as well as artifact uploads.

Verify that the intended Git commit reached the remote and that the intended
DVC artifacts reached their authorized destination. Report any failed or blocked
commit, push or verification explicitly; do not describe a local-only mirror
copy as a completed remote push. Do not request redundant approval for uploads
already authorized by the user.

## Preserve agreed experiment decisions (2026-11-08)

Use the user's already agreed representations, experimental parameters and scope as constraints. If a choice is uncertain or changing it appears necessary, ask before implementation or expenditure. Never silently substitute a different representation. The current two-case comparison is ignition-anchored cone versus freely fitted cone; an ellipsoid is not an authorized substitute. Bulk conversion and local raw-data deletion remain pending explicit user review.
