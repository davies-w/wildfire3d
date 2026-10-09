# Working practices: what it takes to get a case running, and what bites

Practical findings from actually building and running garden / wildland-urban
interface cases in FDS 6.11.1 + Smokeview 6.11.2 on macOS (Apple Silicon,
x86-64 binaries under Rosetta). Everything here was reproduced, not read off a
spec sheet. Treat it as the list of things worth knowing *before* losing an
afternoon to them.

---

## 1. Getting it running

| | |
|---|---|
| licences | FDS and Smokeview are **public domain** (NIST) |
| repo | `firemodels/fds`, actively maintained |
| macOS install | `FDS-6.11.1_SMV-6.11.2_osx.sh` from GitHub releases |
| architecture | binaries are **x86-64 only** — Rosetta required on Apple Silicon |
| XQuartz | **not needed**; Smokeview is a native Cocoa build |
| build | none — binary distribution ships `bin/fds` and `smvbin/smokeview` |

**Installer gotcha:** the `.sh` installer is interactive and *blocks* with no
TTY. Feed it stdin: `printf '2\n' | bash installer.sh`. Use `bash`, not `sh`
(macOS `sh` is bash in POSIX mode and breaks its bash-isms).

**Architecture of the two programs — important:**

FDS and Smokeview are **completely separate programs that communicate only
through files on disk.** FDS (Fortran) writes `.smv`, `.s3d`, `.sf`, `.bf`,
`.prt5`, `.ter`, `.csv`; Smokeview (C) reads them and draws pixels. Neither
calls the other.

The practical consequence: **when a colour or appearance problem appears, it is
usually the renderer, not the solver.** FDS has no concept of colour.
Re-rendering does not require re-solving, and vice versa.

---

## 2. What worked well

- **3-D transient CFD** with buoyant plumes, smoke transport, radiation and
  combustion. The plume physics is real and looks right.
- **Level-set wildland fire spread** (`&MISC LEVEL_SET_MODE=4`) — Rothermel-
  Albini spread over a terrain surface, cheap enough to run a whole garden.
  Modes 1-4 trade off: 1 = no fire, 2 = frozen wind, 3 = no fire, 4 = fully
  coupled wind and fire.
- **Lagrangian firebrands** — generation from a burning surface via
  `EMBER_YIELD` on the surface, transport with `DRAG_LAW='DISK'`, and particle
  temperature as an output.
- **Ingition by temperature** — `IGNITION_TEMPERATURE` on a surface, with
  `&BNDF QUANTITY='WALL TEMPERATURE'` to watch surfaces approach ignition.
- **Arbitrary geometry** — `&OBST` for axis-aligned boxes, `&GEOM` for
  arbitrary triangulated surfaces (closed solids get filled; open ones make
  pressure zones).
- **Distinct vegetation as solid fuel objects** — a hedge or tree as an `&OBST`
  with its own density, conductivity, ignition temperature and `HRRPUA`. Not
  physically resolved vegetation, but real distinct objects that ignite and
  radiate.

### Scale actually achieved

| case | size | cost |
|---|---|---|
| 40 × 40 × 12 m, 1 m cells (19,200 cells), 120 s | ~2,000 steps | ~5 min |
| 40 × 40 × 24 m, 1 m cells (38,400 cells), 120 s | 2,519 steps | ~7 min |

with ~1,000-2,000 Lagrangian particles and multi-GB volume output.

---

## 3. Genuine limits

- **Uniform cells within a mesh.** No grading. `TRNX`/`TRNY`/`TRNZ` exist for
  piecewise-linear stretching in 1-2 directions, but the manual caps cell aspect
  ratio at ~2-3 and warns that LES eddy formation is limited by the *largest*
  cell dimension — so you cannot make the sky into a few giant cells.
- **Physics-resolved vegetation needs ~0.05 m cells.** Tested the Boundary Fuel
  Model at 1.0 / 0.5 / 0.25 m: vegetation burns locally but fire **never
  propagates** at any of them. NIST's own examples use 0.05 m, where a 20 × 8 m
  patch alone is 7.7 M cells. At property scale the level-set model is the only
  practical option — with the trade-off that spread is *empirical* rather than
  predicted.
- **Vertical mesh splitting is discouraged** — a bundled example warns "do not
  split in Z until we address cut-face linking issue".
- **Domain too small for the plume.** A ~150 MW fire in a 12 m tall box
  saturates the domain with soot. Raising to 24 m helps a lot.

---

## 4. Bugs and quirks encountered (not limits)

| issue | detail |
|---|---|
| **`&GEOM` + particles = segfault** | `part_mp_move_part` → `complex_geometry_`. Any `&GEOM` an airborne particle touches kills the run. Eliminated by converting all `&GEOM` to `&OBST`. Serious for WUI work, since firebrands and buildings are the point. |
| **Smokeview draws terrain outside the surface system** | The `.ter` ground is drawn with its own colour, ignoring every `SURFACE` property. Produces an olive skirt at the base of every obstruction that is easily mistaken for geometry. Fix: strip the two-line `TERRAIN` block from the `.smv`. The `.ter` *file* must stay on disk. |
| `XYZVIEW` segfaults | SIGILL under Rosetta with both comma and space syntax. Use the preset directions (`VIEWXMAX`/`VIEWYMAX`/`VIEWZMAX`) or a viewpoint from an `.ini`. |
| multi-frame renders crash | Intermittent crashes rendering many frames of large volume files in one invocation. **Render one frame per invocation.** |
| `-load_soot`, `-smoke3d` | Documented as startup flags but do nothing in `-runscript` batch mode. |
| smoke opacity is GUI-only | No script command to set it. Batch renders saturate to a black mass. Workaround: render the flame and the soot as separate passes and blend them in post. |
| `.smv` is regenerated every solve | Any post-solve patch (e.g. the terrain strip) must be **re-applied after each re-solve**. |

---

## 5. Input-file gotchas worth writing down

- **`smokeview -runscript <name>` requires `<name>` to be the casename** — it
  looks for `<name>.ssf` *and* loads `<name>.smv`. An arbitrary script name
  fails with "unable to open `<name>.smv`" and renders nothing.
- **Use `RGB=` for colours, not names.** `BROWN` is X11 brown = RGB(165,42,42),
  a brick **red**. `BURLYWOOD` and `DIMGRAY` don't exist. Multi-word names need
  spaces: `LIGHT BLUE`, `DARK GRAY`.
- **`&SPEC ID='WATER VAPOR'` is required** if any material has moisture.
- **`IGNITION_TEMPERATURE` and `REFERENCE_TEMPERATURE` are mutually exclusive.**
  At coarse resolution use the former plus `CONDUCTIVITY` / `SPECIFIC_HEAT` /
  `DENSITY` — this is what the FDS developers recommend over reaction
  parameters.
- **Level-set burn rate comes from the fuel model, not `HRRPUA`.** With
  `ṁ''f = (1 − char_fraction) · load / burn_duration`, load 0.6 kg/m² and the
  default burn duration gives ~1,250 kW/m² — which produced 1.9 GW and blew the
  mesh up. Also: the reaction's **heat of combustion scales the whole fire**, so
  using propane (46.5 MJ/kg) instead of wood (17.3 MJ/kg) over-predicts by 2.7×.
- **`HRR` devices need `XB` coordinates.**
- **`EMBER_GENERATION_HEIGHT` is the lofting model** in level-set mode. Without
  it, embers spawn *on* the burning surface, in the boundary layer where the
  vertical velocity is ~0, and never get lifted. It accepts a range, e.g.
  `EMBER_GENERATION_HEIGHT = 1.0, 8.0`.
- **Ember temperature**: a firebrand material with a huge `SPECIFIC_HEAT` (as in
  NIST's `LS4` example) only works if the ember is *born* hot. For
  surface-generated embers set `INITIAL_TEMPERATURE` on the `PART` — it does
  apply to generated particles. Without it they sit at 20-60 °C and cannot
  ignite anything.

---

## 6. Verdict

**FDS is a capable, well-documented, genuinely open 3-D fire model, and it runs
fine on a laptop.** For this property-scale WUI use case:

- **Good for:** plume and smoke structure, radiant heat to surfaces, surface
  temperature and ignition thresholds, firebrand transport, general
  "what does the flow near this building look like".
- **Not good for:** resolved vegetation and physics-predicted fire spread at
  property scale, or photorealistic buildings alongside airborne particles
  (the `&GEOM` crash).

The honest summary is that FDS will tell you a great deal about *what happens
around* a building in a fire, and comparatively little about *how the vegetation
burns* unless you can afford 0.05 m cells.
