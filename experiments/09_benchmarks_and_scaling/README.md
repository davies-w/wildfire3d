# 09 — Benchmarks and thread scaling

**Question.** How much faster can this actually be made, and where should the
effort go?

**Setup.** A fixed 153,600-cell bench deck (`bench.fds`), solved identically
under different builds and thread counts. Numbers are from
`scaling.py` / `scaling_arm.py`.

**Results.**

Rosetta (the stock x86-64 NIST binary):

| threads | time (s) | speed-up |
|---|---|---|
| 1 | 262.0 | 1.00× |
| 2 | 199.6 | 1.31× |
| 4 | 246.9 | 1.06× |
| 8 | 276.6 | **0.95×** |

Native arm64:

| threads | time (s) | speed-up |
|---|---|---|
| 1 | 171.1 | 1.00× |
| 2 | 139.9 | 1.22× |
| 4 | **122.1** | **1.40×** |
| 8 | 139.2 | 1.23× |

**Conclusions.**

1. **Build native.** 1.60× from translation alone, free.
2. **Four threads, not eight.** 8 threads is *slower than one* on this machine —
   it is a throttling limit, not a physics limit. A real solve corroborates it:
   `wick3c` at `OMP_NUM_THREADS=8` used only ~1.9 effective cores.
3. **Not I/O bound.** ~31 KB per step against 0.686 CPU-seconds per step.

Full argument, including why cloud and GPU were rejected, is in
`docs/performance.md`.

**Files.** `bench_builds.py` (build comparison), `scaling.py`,
`scaling_arm.py`, `ec2_price.py` (cloud pricing), `blob_audit.py` and
`compress_test.py` (output volume and compressibility — the measurements that
set the storage policy in `docs/storage.md`).
