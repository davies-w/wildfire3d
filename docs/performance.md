# Performance: building FDS native, and what actually makes it faster

Measured on an M2 MacBook Air (8 logical CPUs, 4 performance cores). Every
number here is from a real run on the meshes in `experiments/`, not a benchmark
in the abstract.

## The single biggest win: build FDS native

The NIST macOS binary is **x86-64 only**, so on Apple Silicon it runs under
Rosetta. Building FDS natively for arm64 is worth more than every tuning knob
combined.

| build | threads | s/step on the bench mesh |
|---|---|---|
| NIST binary under Rosetta | 1 | 273.4 |
| **native arm64** | 1 | **171.1** (**1.60×**) |

That is a 1.60× speed-up from translation alone. Build recipe:

- Homebrew `gcc` (16.2.0) and `open-mpi` (5.0.11), both native arm64
- `mpifort` wraps gfortran; stage 1 runs `build_thirdparty_libs.sh`, stage 2
  repeatedly runs `make` until it completes
- **HYPRE and SUNDIALS were not found and are not linked.** The build is sound
  without them — validated by comparing HRR against the stock binary
  single-threaded, which agrees to 1e-6 over the first 5 s.

## Thread scaling: 4 is the optimum, and 8 is *slower than 1*

| threads | bench time (s) | speed-up |
|---|---|---|
| 1 | 171.1 | 1.00× |
| 2 | 139.9 | 1.22× |
| **4** | **122.1** | **1.40×** |
| 8 | 139.2 | 1.23× |

Two independent measurements agree. On Rosetta scaling was worse still: 1 thr
262.0 s, 2 thr 199.6, 4 thr 246.9, **8 thr 276.6 — slower than one thread**.

A real solve bears this out: `wick3c` accumulated 13,400 CPU-seconds over 160 s
of simulated time at `OMP_NUM_THREADS=8`, i.e. only **~1.9 effective cores**.
The machine throttles under sustained load — a re-run of the same benchmark gave
`fds` 313.6 s where it had been 249.0.

**Recommendation: `OMP_NUM_THREADS=4` for long runs.** Using 8 wastes power,
generates heat, and on this laptop is actively counterproductive.

## It is not I/O bound

~31 KB written per step against 0.686 CPU-seconds per step. Output volume is
never the reason a run is slow; the solver is.

## Cloud: rejected, and the arithmetic is why

Cloud was priced properly rather than dismissed. Cheapest on-demand rates found:
c7g $0.03625/vCPU-hr, c8g $0.03988, c7i $0.04462, c7a $0.05132; Oracle Ampere
A1 $0.01/OCPU-hr; Hetzner CCX33 €0.066/hr.

It still loses. The native arm64 build already delivered **2.27×** for free
(Rosetta-8-thread to arm64-4-thread), and scaling tops out at 1.40× on four
threads — so a fat cloud instance is poor value, and a fast one only buys
roughly 1.3–1.8× over what the laptop now does. **Cloud is only worth
considering for fidelity** — affording a finer mesh — never for speed.

Oracle's Always Free tier was also cut in June 2026 from 4 OCPU/24 GB to
2 OCPU/12 GB, which removes the one genuinely free option.

## GPU: rejected on the evidence

FDS's GPU work is the **FireX** branch (NIST, 2023+). It accelerates **only the
global pressure Poisson solve**, via HYPRE/UGLMAT — and NIST states that this
solver is *"generally slower than the default FFT pressure solver in FDS"*. No
finite-rate chemistry, transport or radiation on GPU.

It targets large multi-rank domains, which is the opposite of these small
meshes. Wrong regime, wrong solver, no benefit to be had.
