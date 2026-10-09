# wildfire3d

Property-scale wildfire physics: 3-D, time-dependent simulation of fire
approaching a single home — the flame front, the embers it throws, and whether
the building ignites.

Built on **NIST FDS** (Fire Dynamics Simulator). This repository is the
**apparatus and the findings**, not a solver: input decks, the scripts that run
and analyse them, the rendered results, and the notes that explain what the runs
show and where the tool's limits are.

## Start here

| document | what it answers |
|---|---|
| [`docs/physics-engine.md`](docs/physics-engine.md) | Which open-source model, and why FDS. Literature survey. |
| [`docs/working-practices.md`](docs/working-practices.md) | Every gotcha found the hard way. Read before writing a deck. |
| [`docs/performance.md`](docs/performance.md) | Native arm64 build, thread scaling, why cloud and GPU were rejected. |
| [`docs/storage.md`](docs/storage.md) | Where the raw output lives, and why most of it shouldn't be kept. |
| [`docs/focus-fix.md`](docs/focus-fix.md) | Stopping Smokeview stealing focus from a full-screen game on macOS. |
| [`docs/rendering.md`](docs/rendering.md) | The shared animation pipeline: the per-case config, the tools, and what bites. |

## Layout

```
docs/                 the findings
experiments/          one directory per experiment: input, scripts, results
scripts/              shared tooling: engine setup, storage, rendering helpers
paths.py              single source of truth for where the engine lives
FDS/                  the engine and its data — gitignored, see FDS/README.md
```

Each directory under `experiments/` is self-contained — the `.fds` input that
produced it, the scripts that ran and analysed it, and a `README.md` giving the
aim, the numbers, and what was concluded. A reader should be able to take one
experiment directory and reproduce that result without reading anything else.

## Experiments

| # | experiment | question |
|---|---|---|
| 01 | `baseline_garden` | A garden fire with a house in it — does the house catch? |
| 02 | `no_lawn_control` | Control: the same case with the lawn removed. |
| 03 | `vegetation` | Hedge and trees as distinct burning objects. |
| 04 | `fence_and_trees_large` | 60 m domain: fence line, six trees — does the house heat up? |
| 05 | `ember_lofting` | Do firebrands actually leave the boundary layer? |
| 06 | `half_metre_ladder` | 0.5 m cells — a ladder tree ignites. |
| 07 | `wick3_house_ignition` | The headline result: wall temperature to full involvement. |
| 08 | `isolated_ember_ignition` | One ember on a fuel bed, away from any fire. |
| 09 | `benchmarks_and_scaling` | Thread scaling, Rosetta vs native arm64. |
| 10 | `build_validation` | Does the hand-built arm64 FDS agree with the stock binary? |

## Setting up

```bash
python3 scripts/setup_engine.py --dist --build   # FDS itself
python3 scripts/setup_env.py                     # venv: numpy, pillow, dvc
python3 scripts/check_no_hardcoded_paths.py      # lint
```

The engine is **not committed** — it is a large third-party tree plus build
output, so it is checked out into `FDS/` (gitignored) by a recorded recipe
rather than vendored. That directory holds the checkout, the solver output and
the case data together. See [`FDS/README.md`](FDS/README.md).

Scripts never hardcode that location. Everything resolves through `paths.py`,
which defaults `FDS_ROOT` to `FDS/` and honours `WILDFIRE3D_FDS` to point at a
checkout somewhere else.

## Getting the data

Raw solver output is versioned with **DVC** and stored in a public Hugging Face
bucket. Pulling needs **no account and no credentials**:

```bash
dvc pull
```

Details, and the reasons most of the raw output is deliberately *not* kept, are
in [`docs/storage.md`](docs/storage.md).

## Running a case

Input decks are plain FDS. The pipeline is `fds`, then a mandatory post-solve
terrain strip, then Smokeview.

```bash
# 1. solve (4 threads -- 8 is slower on this hardware, see docs/performance.md)
OMP_NUM_THREADS=4 FDS/install/bin/fds mycase.fds

# 2. strip the TERRAIN block from the regenerated .smv (see working-practices.md)
python3 scripts/strip_terrain.py mycase

# 3. render -- renderers are per-experiment; see experiments/*/README.md
```

**Use 4 threads, not 8.** On this hardware 8 is slower than 1. See
`docs/performance.md`.

## Licence

Public domain, matching FDS itself. The solver is NIST's work; the decks,
scripts and notes here are released the same way.
