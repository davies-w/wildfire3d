# 07 — The house ignites

**Question.** Does the building itself catch? Not "is it hot", but does the wall
cross its ignition temperature and stay there.

**Setup.** `wick3c.fds`. 32 × 24 × 12 m, **0.5 m cells** (73,728 cells), 350 s.
Native arm64 build at `OMP_NUM_THREADS=4`, single clean solve, no restart.

**Result.** Wall temperature, read from the `WALL TEMPERATURE` boundary file
over the house's west face (x = 18 plane, y 8–16, z 0–3.5 — 136 cells).

| t (s) | mean | max | cells above 350 °C |
|---|---|---|---|
| 48 | 23.5 °C | 29.2 °C | 0 / 136 |
| 100 | 30.7 | 51.1 | 0 / 136 |
| 148 | 40.9 | 82.9 | 0 / 136 |
| 200 | 108.0 | **317.6** | 0 / 136 |
| 248 | **589.0** | **1022.2** | **113 / 136** |
| 300 | 975.6 | 1410.4 | 136 / 136 |
| 348 | 1055.7 | 1450.6 | 136 / 136 |

**Yes.** Ignition onset falls between t = 200 and t = 248 s; by t = 300 s the
whole wall is above the 350 °C wood threshold. The rise is not gradual — slow,
then nearly vertical, which is what thermal-feedback ignition looks like.

**Cost.** 350 s of simulated time in **71.0 min**, 16,151 steps, **0.264 s/step**.
Re-run under the pipeline: **65.1 min**, 16,091 steps, **0.242 s/step**.

## The animation

`ignition_data.gif`, 24 frames, t = 16–348 s. Colour is a function of the
**measured** temperature, not of anything Smokeview chooses:

- below a surface's ignition temperature → its original colour
- at or above → orange, deepening to red

Per-surface temperature comes from the `.bf` via `fds2ascii`
(`scripts/surface_temp.py`); the colour is written into the `.smv` SURFACE table
and the frame rendered with no boundary file loaded, so Smokeview supplies only
geometry, flame, embers and smoke. Every colour is printed when rendering.

**Only the house is coloured**: `WOOD WALL` (350 °C) and `ROOF` (550 °C). The
canopy, trunks, fence and grass keep the deck's colours and show themselves
through the flame volume. This is the standing convention, and it matters here:
colour is written per SURFACE *name*, so painting `CANOPY` repaints the wick
tree and every wild tree at once.

| t | house |
|---|---|
| 16–180 | below threshold |
| 200 | 343 °C — wall just under 350 |
| 220 | 677 °C — ignited |
| 300 | 1,424 °C |
| 348 | 1,470 °C |

## What was wrong before, and why

An earlier version let Smokeview map the burning-rate boundary file onto its
own palette, then applied a red-versus-blue pixel test to the result. Measured:

- pass B rendered the scene **`[0,0,255]` pure blue** almost everywhere
- the **house wall never changed colour in any frame**, including t = 350 where
  its face is 1451 °C and fully above threshold

The headline result was absent from its own animation. The colour was a pixel
heuristic on Smokeview's palette, not a temperature. Fixed by the above.

The **salmon quad was never a bug**: it is the `WOOD WALL` face at 0.8 shading
(`0.80 × (222,184,135) = (178,147,108)`, exact). An earlier claim that it was a
pass-to-pass rendering difference was wrong.

## Embers never lofted (found late)

`wick3c.fds` was missing `EMBER_GENERATION_HEIGHT` on the ember-generating
surface. It is the lofting control, it is a **`&SURF`** property rather than
`&MISC`, and it defaults to **-1**, which means "spawn on the surface". So
every ember was born at ground level and stayed there.

Measured from the `.prt5` particle file (`read_embers.py`):

| run | max ember height | embers above 2 m |
|---|---|---|
| `wick3c` (no keyword) | 0.25 m | 0 of 45 output steps |
| exp 05 `garden_loft` (keyword set) | 12.00 m | 261 at t = 40 s |

The fix was already known -- exp 05 established it and exp 03 and 04 carry it --
but it was lost when the wick cases were rewritten in a terser `&SURF` form that
kept `EMBER_YIELD` and `PART_ID` and so looked complete.

The deck has it. The original 350 s run predated the line, so its animation
showed ground-level embers. **The run recorded here was redone with the keyword
present**, so this animation does include lofted embers; the earlier decision
not to re-run was overridden when every experiment was rebuilt as a pipeline.

Note that lofting is transient even when it works: in exp 05 every ember is
back on the ground by t = 112 s, so it happens only around the peak of the fire.

## Gotchas established here

- **`ZOOM` must come *after* `SETVIEWPOINT`**, in a second `LOADINIFILE`.
  Before it, the viewpoint overwrites it. Without it the render truncates the
  foreground (777 px of geometry off the bottom edge, 38 px off the right).
- **Surface colours must go in the case's own `.smv`.** A side-car `.smv` loaded
  with `LOADSMV` is ignored for colour — patched correctly in the file and still
  rendered in the base colour.
- **`LOADSMV` does not work for multi-frame rendering.** Changing colours means
  re-reading the `.smv`; after the first `LOADSMV` the data volumes stop
  reloading and 10 of 12 frames came out blank. Hence one launch per frame.
- **`SMOKEPROP` is a mass extinction coefficient in m²/kg**, of order 10³–10⁴.
  Values near 1 are effectively transparent. At t = 300, 2500/1200/600 gave no
  usable frame, 300 leaves 13737 warm pixels and a visible grey plume, 0 leaves
  11977 and almost no smoke.
- **Smokeview shades surfaces**, so a rendered pixel is the table colour scaled
  — usually ×0.8, but up to ×1.05 on lit faces.
- **Smokeview segfaults (exit -11) on the occasional frame**; the renderer
  retries missing frames rather than lose a frame of animation silently.

## Pipeline

`dvc repro experiments/07_wick3_house_ignition/dvc.yaml` runs four stages:
solve, boundary, render, validate. `dvc.lock` is committed. Solver output goes
to `data/`, this case's settings are in `render.json`, the saved viewpoint is
`view.ini`. The `.s3d` volumes are uncached.

Solve cost on the re-run: **65.1 min**, 16,091 steps, **0.242 s/step** — against
71.0 min and 16,151 steps originally, same deck. FDS is not bit-reproducible
across builds, so two step counts agreeing to within 0.4 % is as close as this
gets.

## Files

- `wick3c.fds` — the deck. `wick3.fds` is the 200 s variant, kept as a record,
  not part of the pipeline.
- `render.json` — this case's config for the shared render pipeline
- `view.ini` — the saved viewpoint
- `scripts/` — the one-off scripts: the diagnostic ones that established the
  findings here (`diag_salmon.py`, `diag_surfaces.py`, `diag_wall_ignition.py`,
  `probe_bf.py`) and the run drivers. `make_gif.py` was deleted — it had become
  a byte-identical copy of the shared `scripts/make_gif.py`.
- `results/` — `ignition_data.gif`, `i_140.png`, `i_300.png`

See `docs/rendering.md` for the config format and the gotchas.
