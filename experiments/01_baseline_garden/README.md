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
Results: `gh_026.png`, `gh_115.png` (t = 26 s, 115 s), `fire_3d.gif`.
