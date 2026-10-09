# 01 — Baseline garden fire with a house

**Question.** Light a garden fire with a house standing in it, and see whether
the fire does anything to the building.

**Setup.** `garden_house.fds`. 40 × 40 × 12 m domain, 1 m cells (19,200 cells),
120 s. The house is a blocky `&OBST`. The lawn is a level-set fuel region
(`LEVEL_SET_MODE=4`), so spread is the Rothermel–Albini model rather than
resolved vegetation — see `docs/working-practices.md` for why that is forced at
this cell size.

**What happened.** Peak heat release rate **138 MW**, then the fire **decays to
0.34 MW**. The lawn burns off and does not sustain.

**Conclusion.** At 1 m cells a grass fire will not carry. This is the
motivation for experiment 02: removing the lawn to see whether the transient
peak or the sustained phase is doing the heating — and for the move to 0.5 m
cells in 06 and 07.

**Files.** `run_case.py` solves; `patch_smv_colors.py` and `identify_skirt.py`
are renderer fixes (see `docs/working-practices.md`, terrain skirt).

The pipeline is `dvc.yaml`: `solve`, `boundary`, `render`. `dvc repro` runs all
three, from the deck to the gif. `render.json` holds the case settings and
`view.ini` the saved viewpoint.

Results, all produced by `scripts/render_animation.py`: `ignition_data.gif`
(18 frames, 4–120 s) with `i_040.png` and `i_120.png`.

**Only the walls are coloured, and that is deliberate.** A patch dump shows 13
boundary patches: four wall faces, one patch on the wall top, and eight on the
ground. Nothing appears above z = 4 m, so the gable roof — built as `&GEOM` —
emits no boundary data and cannot be measured; colouring it would be invention.
It is also why the wall patches read 0–4 m rather than the 3.5 m in the deck:
FDS snaps `&OBST` to the 1 m grid.

The house does not ignite in this case: the wall peaks at 120 °C at t = 20 s,
then cools to 46 °C by 120 s, against an ignition temperature of 350 °C.
