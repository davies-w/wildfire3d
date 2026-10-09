# 03 — Vegetation as distinct burning objects

**Question.** Can trees and a hedge be represented as things that ignite and
radiate, without resolving individual leaves?

**Setup.** `garden_veg.fds` (hedge + 5 trees) and `garden_veg_obst.fds`. Same
40 × 40 × 12 m, 1 m cells, 120 s as experiments 01–02. Vegetation is modelled as
`&OBST` solids with their own density, conductivity, ignition temperature and
`HRRPUA` — solid fuel objects with fire properties, not resolved foliage.

**What happened.** Peak **171 MW**, sustained **20–58 MW** — a step change over
01 and 02, because vegetation is a fuel source the lawn was not.

**Conclusion.** Distinct burning objects are a workable middle ground at 1 m
cells. They are not physically resolved vegetation — the burning is a prescribed
release rate, not pyrolysis — but they are real objects that ignite at a
temperature, and they change the answer. The honest limitation is that *when*
they ignite is set by us, not predicted; see experiment 07 for what happens at
0.5 m where a tree can take over on its own.

**Files.** `composite_smoke.py` blends flame and soot passes (the smoke-opacity
workaround — `docs/working-practices.md`); `diag_smoke.py` diagnoses the blend.
Results: `c_030.png` (composited), `ls_100.png` (level-set spread).
