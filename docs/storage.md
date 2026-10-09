# Storage: raw FDS output, DVC, and Hugging Face buckets

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
