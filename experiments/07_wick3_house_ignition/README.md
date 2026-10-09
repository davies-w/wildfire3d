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

## The animation

`ignition_data.gif`, 12 frames, t = 40–348 s. Colour is a function of the
**measured** temperature, not of anything Smokeview chooses:

- below a surface's ignition temperature → its original colour
- at or above → orange, deepening to red

Per-surface temperature comes from the `.bf` via `fds2ascii` (`ign_state.py`);
the colour is written into the `.smv` SURFACE table and the frame rendered with
no boundary file loaded, so Smokeview supplies only geometry, flame, embers and
smoke. Every colour is printed when rendering.

Surfaces that change colour: **CANOPY** and **TRUNK** (the wick tree, ignition
250 °C), **WOOD WALL** (350 °C), **ROOF** (550 °C), **FENCE** (300 °C).

| t | ignited |
|---|---|
| 40–92 | — |
| 140–200 | canopy (and fence) |
| 220–348 | all five |

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

The deck now has it. **The recorded 350 s run predates the line**, so the
animation shows ground-level embers and its ember behaviour should be ignored.
A re-run was judged not worth ~71 min, because the question the fix answers is
already answered from exp 05's existing output.

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

## Files

- `build_clean.py` — writes the deck
- `run_clean_arm.py` — solves, native arm64, 4 threads
- `analyse_clean.py` — the wall-temperature history above
- `strip_terrain.py` — **mandatory** post-solve (see `docs/working-practices.md`)
- `ign_state.py` — per-surface temperature from the `.bf`; verifies all 38
  patches map to exactly one surface
- `ign_colour_render.py` — colours the geometry and renders the animation
- `validate_animation.py` — completeness, distinctness and colour truth
- `measure_framing.py`, `try_zoom.py`, `try_smokeprop.py` — the framing and
  smoke sweeps behind the values used
- `dump_patches.py`, `diag_salmon.py`, `diag_surfaces.py`, `census.py` — the
  measurements that established the above
