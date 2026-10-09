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

## Pipeline

`dvc repro experiments/03_vegetation/dvc.yaml` runs the whole experiment: both
decks solved together in one stage, then a boundary stage and a render stage per
case. `dvc.lock` is committed. Every solver output lands in `data/`, one
subdirectory per case — `data/garden_veg/` and `data/garden_veg_obst/` — because
the boundary reader and the renderer both write fixed filenames that would
collide if the two cases shared a directory. Settings are in `garden_veg.json`
and `garden_veg_obst.json`; the saved viewpoint is `view.ini`.

Both decks are the same garden apart from the roof and the vegetation. In
`garden_veg` the roof is a `&GEOM` gable and the trees are level-set vegetation;
in `garden_veg_obst` the roof is an `&OBST` slab stack and the canopies are
`&OBST` solids, which is the variant this experiment is about.

**Colourable surfaces.** A patch dump of each case gives the mapping. In
`garden_veg` the roof emits no boundary patches at all — `&GEOM` geometry never
does, the same limitation as experiment 01 — so only the walls can be coloured
from measurement. In `garden_veg_obst` the roof is a solid from z 4 to 6 m and
emits patches, so both walls and roof are measurable. The hedge (x 15–16,
z 0–2 m) and the five trunks also emit patches and could be added to either
config with a box each; they are left in their deck colours, as in 07.

**Measured result.**

| t (s) | `garden_veg` wall | `garden_veg_obst` wall | `garden_veg_obst` roof |
|---|---|---|---|
| 40 | 190 | 145 | 170 |
| 60 | 278 | 246 | 252 |
| 90 | **344** | 337 | 332 |
| 100 | 329 | 349 | 325 |
| 110 | 325 | **360** | 315 |
| 120 | 309 | 359 | 300 |

Ignition temperature is 350 °C for the wall and 550 °C for the roof. The
`garden_veg` wall peaks at 344 °C and never ignites. The `garden_veg_obst` wall
crosses 350 °C between t = 100 and 110 s, so the house ignites late; its roof
never approaches 550 °C. Both gifs show the house coloured from measured
temperature: `results/veg/ignition_data.gif` stays tan throughout,
`results/obst/ignition_data.gif` turns the walls red in the last 20 s.
