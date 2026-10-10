# 08 — One ember on a fuel bed, away from any fire

**Question.** Take the flame front away entirely. A single firebrand lands on a
fuel bed — does it ignite it, and after how long?

**Setup.** Three families of deck, all small:

- `ember_test.fds` — an ember landing on a garden fuel bed
- `LS4_ember_ignition.fds` — the minimal single-ember case, derived from NIST's
  `LS4` level-set example
- `bfm_res_test.fds` — the **Boundary Fuel Model** resolution experiment, at
  1.0 / 0.5 / 0.25 m

**What happened — the most useful negative result in the project.** At every
resolution tested, vegetation under the Boundary Fuel Model **burns locally but
the fire never propagates**. Not at 1.0 m, not at 0.5 m, not at 0.25 m. NIST's
own examples that work use **0.05 m** cells, where a 20 × 8 m patch alone is
7.7 million cells — out of reach at property scale.

**Conclusion.** Physics-resolved vegetation combustion is not available at this
scale. The level-set model used everywhere else in this repository is the only
practical option, with the honest trade-off that spread becomes *empirical*
rather than *predicted*. This experiment is why that trade is made explicitly
rather than by omission.

The ember cases themselves confirm the mechanism the literature predicts — a
minimum ember size below which stored heat cannot initiate ignition, and an
ignition delay that grows as the ember shrinks — which is why the ember chain
gets as much attention as the flame front.

**Files.** `scripts/make_test_variants.py` generated the resolution variants;
they were not kept, so that sweep is not reproducible from this repository.
`scripts/geom_canopies_to_obst.py` and `scripts/probe_geom.py` are the geometry
tools below.

## The ember_test deck segfaults, and why

`ember_test.fds` has **never completed a run**. It stops at about step 600 with
SIGSEGV, on both the older engine build (its `run.log` in the case directory
shows the same fault at the same step) and the current one. Nothing caught it
before because `scripts/run_fds.py` printed the solver's exit code and then
returned success anyway, so DVC wrote a lock file for a truncated run. That is
now fixed: a solver that exits non-zero fails the stage.

The cause was isolated by running three probe decks, all in `data/` and so not
committed:

| probe | change | result |
|---|---|---|
| `probe_ember` | firebrand generation off | **still segfaults** |
| `probe_nogeom` | all six `&GEOM` blocks removed | completes, 859 steps, t=40 s |
| `ember_test_obst` | five `&GEOM` canopies → `&OBST`, roof left as `&GEOM` | **still segfaults** |
| `probe_noroof` | that variant with the roof `&GEOM` removed too | completes, 822 steps, t=40 s |

So the recorded explanation — "`&GEOM` plus airborne particles" — is wrong in
its first half: switching the embers off does not help. It is the geometry, and
in this deck specifically the gable **roof**. Experiment 03's `garden_veg` keeps
a `&GEOM` roof and runs to completion with embers, so this is deck-specific
rather than a blanket rule about `&GEOM`.

## Pipeline

`dvc repro experiments/08_isolated_ember_ignition/dvc.yaml` runs four stages.
`dvc.lock` is committed. Two decks are solved and two are not:

- `solve` — `ember_test_obst.fds`, generated from `ember_test.fds` by
  `scripts/geom_canopies_to_obst.py --all`, which rewrites every `&GEOM` as its
  bounding-box `&OBST`. That is the only form proven to run here. The trade is
  shape: the gable roof becomes a box. Experiment 03's `garden_veg_obst`
  instead uses three stacked slabs, which keeps a stepped silhouette; that is
  the better substitution if the shape matters.
- `solve_variants` — `LS4_ember_ignition.fds` and `bfm_res_test.fds`. Neither
  requests boundary output, so neither can be coloured from measurement and
  neither is rendered. They are solved so the numbers above can be reproduced
  from the decks.
- `boundary`, `render` — the house, from measured temperature.

**Measured.** Over 40 s the wall peaks at 161 °C at t=36 s and the roof at
171 °C; nothing approaches the 350 °C threshold. The house is scenery in this
experiment — the fire is a single ember on a fuel bed — and the gif shows the
burning front and embers over the ground, `results/ignition_data.gif`,
14 frames.
