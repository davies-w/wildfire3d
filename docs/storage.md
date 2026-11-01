## Direct uploads without a persistent cache (2026-11-01)

The project command for **DVC push** is now:

```sh
.venv/bin/python scripts/dvc_hf.py push
```

It uses the reviewed plan from the preceding metadata operation, stored locally
in `experiments/43_repository_preservation/results/direct-hf/plan.json`.
The plan is private bookkeeping, not a portable substitute for Git-tracked DVC
metadata. Push it before starting another metadata operation, or save it and
pass `push --plan PATH` explicitly.

For a pipeline stage whose outputs already exist:

```sh
.venv/bin/python scripts/dvc_hf.py commit experiments/NAME/dvc.yaml:STAGE
.venv/bin/python scripts/dvc_hf.py push
```

This updates output hashes in `dvc.lock`, without executing the stage. It does
not certify that dependencies reproduce those bytes, and does not update
recorded dependency hashes. For a real rerun, execute and validate the pipeline
first. Outputs marked `cache: false` are omitted from this upload command.

To reconstruct an upload plan from existing pointers/locks on another checkout:

```sh
.venv/bin/python scripts/dvc_hf.py plan experiments/NAME/historical-files.dvc
# Or: scripts/dvc_hf.py plan experiments/NAME/dvc.yaml:STAGE
.venv/bin/python scripts/dvc_hf.py push
```

This checks local bytes against the recorded hashes and fails on changes; it
never silently redefines an existing artifact. Multiple records are accepted.

For historical artifacts or external/source inputs:

```sh
.venv/bin/python scripts/dvc_hf.py track path/to/input
.venv/bin/python scripts/dvc_hf.py push
```

This writes a standard `.dvc` pointer. Do not use it inside an existing output:
update the owning pipeline instead. The repository-wide adoption uses grouped
`historical-files.dvc` pointers at original paths, not a second exported copy.
`adopt-audit` is the one-time migration of the recorded audit, not a substitute
for refreshing a future audit.

Ordinary `dvc add` normally populates DVC's cache; it does more than write a hash.
This wrapper instead computes the MD5 and standard sorted `.dir` records from
original files and sends those files directly with Hugging Face's bucket API.
Each remote object is checked against the local size and Xet hash; every new
directory record is anonymously downloaded and MD5 checked. The metadata format
is checked against installed DVC. No persistent DVC cache or local mirror is
needed for this upload path. DVC's normal **pull** still uses a local cache.

Financial records, credentials, tool internals and private recovery material are
excluded. A rejected file is not silently redacted or replaced. Inspect the
local plan's `excluded` list. Never describe exclusions or unverified older
records as fully backed up. These checks verify the scoped plan, not every
historical Git revision or every pre-existing DVC object.

Commit and push source, `.gitignore`, `.dvcignore`, `.dvc` pointers and changed
pipeline/lock files after verification. The historical experiment 36 cycle has now been repaired with the user's
explicit approval: six dependency links were removed and the 57 stages in the
cyclic component were frozen. Original definitions and lock records are retained
in `docs/historical-dvc-dependencies.json`. `dvc dag` loads successfully. These
stages are historical snapshots; removing links reduces DVC's ability to detect
changed inputs, and freezing disables automatic reruns. Scientific outputs and
stage commands were not changed.

Normal DVC pull is supported by the metadata. For a scoped independent restore
check, use an **empty directory below this repository**:

```sh
.venv/bin/python scripts/dvc_hf.py restore \
  --destination .artifact-staging/restore-example \
  experiments/42_stacked_gru64/historical-files.dvc
```

This uses unmodified `dvc pull` in an isolated no-SCM checkout, then independently
checks every restored file's MD5. It refuses a nonempty destination. It does not
claim to restore missing external symlink targets, private records or every
old Git revision. Normal DVC pull creates a cache; the scoped test uses hardlinks
where supported to avoid a second physical copy.

The remaining sections record older
storage workflows; their local-mirror and export-copy instructions are
historical and must not be used for new pushes.

# Storage: raw FDS output, DVC, and Hugging Face buckets

## Current local-storage policy (2026-10-31)

Keep original experiment data, simulation outputs, datasets, and recent models
and checkpoints locally. The public Hugging Face archive remains the off-machine
copy; budgets/financial records and credentials must never be uploaded there.

The former persistent local `mirror` remote and redundant project-wide export
folders have been removed after preservation checks. Current scoped upload
helpers for experiments 39–43 and `scripts/push_public_models.py` read selected
objects directly from `.dvc/cache/files/md5`. They create temporary hardlink
staging under `.artifact-staging/` inside this repository and remove that staging
only after a successful upload (and verification where implemented). Failed
staging remains for diagnosis. Never upload the whole cache: it may contain
private objects.

The cache is disposable only after verifying remote preservation and retaining
original workspace files without dependent symlinks. DVC recreates it as needed;
`dvc commit`/`dvc fetch` may be required before subsequent uploads. Do not run old
mirror-based tracking scripts unchanged: those document historical workflows.
Experiment43's `track.py` now uses a temporary repository-local isolated checkout
and adopts outputs without training or creating a persistent mirror.

Experiment43's `data/private/storage-cleanup` retains manifests and historical or
private cache objects not covered by the verified public snapshot. These remain
local and are not public upload targets. Original simulation data and recent
models were not removed. Hardlinks, APFS clones, and other retained references
mean `du` totals do not predict actual disk space reclaimed.

The remainder describes the historical storage setup and prior decisions.

Simulation output is large, and it is **not** reproducible. FDS LES is chaotic:
the same input at different thread counts diverges exponentially, ~2% by t=15–29 s.
A re-run is a *different* run. So raw output has archival value — and a price.

## What is actually big

Measured over the original 1.64 GB of case output:

| suffix | share | what it is |
|---|---|---|
| `.s3d` | 55% | Smoke3D volume dumps (soot / HRR / flame temp) |
| `.restart` | 32% | **scratch** — resume files, worthless once a solve completes |
| `.sf` | 6% | slice temperatures — compresses **7.55×** |
| `.prt5` | 3% | firebrands — compresses 1.45× |
| `.bf` | 1% | wall temperature / burning rate — the ignition evidence |

**87% is `.restart` + `.s3d`.** One is garbage and the other is a render
intermediate: the finished animation is 6.6 MB of gifs against 904 MB of `.s3d`
that produced it.

Policy, therefore:

- **never store `.restart`** — delete after every completed solve
- **store the evidence**: `.bf`, `.prt5`, `.sf` (~65 MB gzipped for the whole
  project). That is the physics you would cite.
- **`.s3d` only if you will re-render at new angles.** Otherwise the animation
  *is* the artifact.
- growth is a choice in the input deck: `SMOKE3D` on/off, `DT_SMOKE3D`,
  `DT_BNDF`, `DT_SLCEF`.

## The remote: Hugging Face Storage Buckets

Bucket: **`wdavies/dvc_storage`** (public). ~12 TB free public storage, Xet
dedup behind it — which matters because consecutive volume frames share most of
their bytes and DVC's content addressing cannot exploit that.

**DagsHub was rejected**: it gives 100 GB, but its remote is not anonymously
readable and reportedly needs collaborator access. R2/B2 give 10 GB free.

### The design is asymmetric on purpose

DVC's `http://` remote is read-only — exactly right for a public archive — so
writes go out through the CLI and reads come in anonymously:

| | how | credentials |
|---|---|---|
| **push** | `dvc push` to a local mirror, then `hf buckets sync` | HF token |
| **pull** | `dvc pull` against the HTTPS resolve URL | **none** |

Anonymous read is *verified*, not assumed:

```
GET https://huggingface.co/buckets/wdavies/dvc_storage/resolve/anon_test/probe.txt
-> 200, correct bytes
```

And the round trip is verified end to end — push, destroy the cache, pull back,
compare md5: **PASS**.

## Why not the S3 API

HF buckets *are* S3-compatible at `https://s3.hf.co/<namespace>`, so DVC's `s3`
remote would work — but the S3 key pair is generated from a separate
"Generate S3 credentials" action in the web UI, and that action was not present.
It does not matter: the CLI plus anonymous HTTPS needs no S3 keys at all.

## Model and training-data public archive (2026-10-30)

The user authorized public bucket storage of all project model weights,
checkpoints and training datasets, excluding budgets and private keys.
`scripts/export_public_models.py` creates the DVC output
`experiments/38_history8_shared64/data/project-model-archive`, including nested
training attempts across the project. Numeric arrays and binary checkpoints
remain byte-identical. Financial JSON fields/commentary are removed; budget
files, private provenance bundles and original tar launch packages are omitted.
The export's manifest records every included file and its SHA-256.

Push this output to the local mirror first, then use
`scripts/push_public_models.py`. This uploads only the objects reachable from
that public output's DVC hash to `wdavies/dvc_storage/wildfire3d`, without
remote deletions. **Do not sync the entire local mirror:** it also contains
private budgets and cloud provenance. Original complete metadata stays local.
