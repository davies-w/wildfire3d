# 04 — Fence line and six trees in a larger domain

**Question.** Does a fence line, a realistic tree count and more room for the
plume change whether the house is threatened?

**Setup.** Two cases, solved together in one stage.

| case | mesh | T_END | what it adds |
|---|---|---|---|
| `garden_tall` | 40 × 40 × 24 m, 1 m cells | 120 s | the same plot as 01–03 with the domain raised from 12 m to 24 m |
| `wick` | 60 × 60 × 24 m, 1 m cells | 160 s | a larger plot, the house moved out to x 32–44 m, and a fence line |

The taller domain was deliberate: a ~150 MW fire in a 12 m box saturates the
domain with soot. Both decks loft embers (`EMBER_GENERATION_HEIGHT = 1.0, 8.0`).

**What happened.** The fire is large and sustained, as before. The two cases
diverge completely at the house.

| t (s) | `garden_tall` wall | `garden_tall` roof | `wick` wall | `wick` roof |
|---|---|---|---|---|
| 40 | 146 | 168 | 42 | 42 |
| 60 | 239 | 264 | 44 | 44 |
| 80 | **361** | 363 | 50 | 49 |
| 100 | 440 | 423 | 55 | 54 |
| 120 | **583** | 460 | 58 | 58 |
| 160 | — | — | **61** | 60 |

Ignition temperature is 350 °C for the wall and 550 °C for the roof.
`garden_tall` crosses 350 °C between t = 70 and 80 s and reaches 583 °C by
t = 120 s — the house ignites. `wick` ends at 61 °C after a third again as long,
and its roof never exceeds 60 °C.

**Correction.** An earlier version of this README concluded that "the house
stays cool" because more fire does not mean more building heating. That is true
of `wick` and false of `garden_tall`: in the tighter 40 × 40 m plot with the
domain raised, the house ignites. Geometry still dominates — the same fire, a
larger plot and a house further away, and the wall is 61 °C instead of 583 °C —
but the earlier conclusion was drawn from the large-plot case alone and stated
as though it covered both. The two runs are not strictly comparable anyway: FDS
is not bit-reproducible across engine builds, and this deck now lofts embers.
The comparison between the two cases *within* this run is sound, since both were
solved by the same binary on the same day.

**Conclusion.** Distance is the dominant term. A sustained multi-megawatt fire
in the same plot ignites the house; move the house into a plot half again as
wide and it stays at ambient-plus-40. That is the result that pushed the two
candidate mechanisms apart — radiant heating to the wall versus direct flame
contact — and made the smaller, closer 0.5 m cases (06, 07) the ones worth
pushing.

**Files.** `house_risk.fds` is superseded: it is `garden_tall` with
`BNDF_DEFAULT=.FALSE.` and `BNDF_OBST=.TRUE.` added to the house surfaces, a
workaround from before the renderer read every patch and mapped them to surfaces
by box. It is kept as a record and is not part of the pipeline. One-off scripts
are in `scripts/`.

## Pipeline

`dvc repro experiments/04_fence_and_trees_large/dvc.yaml` solves both decks in
one stage, then runs a boundary stage and a render stage per case. `dvc.lock` is
committed. Solver output goes to `data/garden_tall/` and `data/wick/`; the
settings are `garden_tall.json` and `wick.json`; the saved viewpoints are
`view_tall.ini` and `view_wick.ini`. The `.s3d` volumes are uncached.

Solve cost: `garden_tall` 385 s, `wick` 914 s, run in parallel — 15.5 minutes
wall clock. Gifs: `results/tall/ignition_data.gif` (18 frames) and
`results/wick/ignition_data.gif` (20 frames), house coloured from measured
temperature. `wick`'s deck sets `BNDF_DEFAULT=.FALSE.` so only the house emits
boundary patches there; its fence and trees cannot be coloured from measurement.
