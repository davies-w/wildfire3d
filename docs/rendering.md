# Rendering a fire case

The animation pipeline is shared. Nothing in `scripts/` knows about any
particular case; everything case-specific lives in a small JSON file beside the
deck. Adding a case means writing that file, not copying a script.

## The case config

`experiments/<name>/render.json`:

```json
{
  "case": "wick4",            // directory under FDS/cases
  "chid": "wick4",            // FDS CHID, i.e. the output file prefix
  "t_end": 300,
  "times": [16, 24, 40],      // frame times; MUST be multiples of DT_BNDF
  "smokeprop": 1800,
  "surfaces": {
    "FENCE": {
      "boxes": [[10.99, 11.49, 0.0, 18.01, 12.01, 2.01]],
      "ignition": 300.0,
      "rgb": [150, 110, 70]
    }
  }
}
```

A box is `(xlo, ylo, zlo, xhi, yhi, zhi)`. Surfes may list several boxes, which
must be disjoint — a patch inside two boxes would let one surface's heat drive
another's colour. `surface_temp.py` checks this and prints any patch that maps
to zero or more than one surface.

`rgb` and `ignition` are copied from the deck's `&SURF` lines. Getting
`ignition` wrong is easy and silent: it was wrong for `TRUNK` in this project
(250 instead of 350), which would have painted that tree as burning 100 °C too
early.

`times` must be multiples of `DT_BNDF` (4 s here) or `fds2ascii` returns NaN
for a window that starts off-grid.

## The tools

| script | does |
|---|---|
| `surface_temp.py <config>` | reads per-surface temperature from the `.bf`, checks the patch mapping, writes `ign_state.json` |
| `render_animation.py <config> [smokeprop]` | colours the geometry from that data and renders the gif |
| `validate_animation.py <config>` | completeness, distinctness, and whether each frame's `.smv` carries the colour its temperature implies |
| `particles.py <config or file.prt5>` | reads ember positions from the `.prt5` |
| `run_fds.py <deck.fds>... [--jobs N] [--threads N]` | solves decks with the native build, in parallel, each in its own case directory |
| `stitch_gifs.py <out.gif> <in1.gif> <in2.gif>...` | pastes gifs side by side, frame for frame |
| `gif_frame.py <in.gif> <index> <out.png>` | extracts one frame, to check what a gif really holds |
| `dump_patches.py <config>` | lists every boundary patch, to build the boxes |
| `strip_terrain.py <casedir> <chid>` | **mandatory post-solve**; FDS rewrites the `.smv` every solve |
| `measure_framing.py <casedir>` | how much geometry touches the frame edge |
| `render_view.py <config> <t> <view> <out.png> [smokeprop]` | one frame from a named viewpoint (XMIN..ZMAX, or a saved one like `iso_b`) |
| `crop_zoom.py <in> <out> x0 y0 x1 y1 [scale]` | crop and magnify, for reading detail |
| `montage.py <out> <cols> <in.png>...` | tile images into one grid, for comparing a sweep |
| `smokeprop_sweep.py <outdir> <v,...> <cfg:t> ...` | the same frame at several `SMOKEPROP` values |

Order, for a fresh solve:

```bash
python3 scripts/strip_terrain.py FDS/cases/<case> <chid>
python3 scripts/surface_temp.py    experiments/<name>/render.json
python3 scripts/render_animation.py experiments/<name>/render.json
python3 scripts/validate_animation.py experiments/<name>/render.json
```

## How it colours

The colour is a function of the **measured** temperature: below a surface's
ignition temperature it keeps its original colour; at or above it goes orange,
deepening to red. The RGB is written into the `.smv` SURFACE table and the
frame is rendered with **no boundary file loaded**, so Smokeview supplies only
geometry, flame, embers and smoke — it never chooses a colour.

## Housekeeping conventions

These are what make two animations comparable. Anything else on screen is a
setting, not the fire, and a difference there will be read as physics.

- **Colour the house only.** Walls and roof. Trees, fence and ground keep the
  deck's own colours and show themselves through the flame and ember volumes.
- **One `smokeprop` for every case.** It is a display setting; if it differs,
  so does the apparent plume density. The default is **300**.
- **Dense early frames, sparse later.** `DT_BNDF` (4 s) is the floor. 8 s spacing
  to about 120 s catches the ember launch and the early spread; 20 s after that
  is enough. From experiment 12:
  `[16, 24, ..., 120, 140, 160, ..., 300]`.
- **Do not reuse a surface name.** Colour is written per surface name, so every
  obstruction sharing one is painted together — and from the first of them to
  ignite. Two trees on the same `SURF_ID` cannot be coloured separately. Give
  anything that should be judged on its own a distinct name.
- **A surface with no boundary output cannot be read.** `BNDF_OBST` unset means
  FDS writes nothing for it, so its temperature is unknown. That is a limit on
  the evidence, not evidence it stayed cool.
- **The live `.smv` is left holding the last frame's colours** after any
  animation pass. `render_view.py` restores the pristine `*.smv.orig` first.

## Two cases side by side

One config per case, both with the **same** `crop_box`, then a plain stitch:

```bash
python3 scripts/render_animation.py experiments/<n>/a.json
python3 scripts/render_animation.py experiments/<n>/b.json
python3 scripts/stitch_gifs.py experiments/<n>/results/side_by_side.gif \
    experiments/<n>/results/a/ignition_data.gif \
    experiments/<n>/results/b/ignition_data.gif
```

Extra config keys, all optional:

| key | effect |
|---|---|
| `crop_box` | pin the crop rectangle `[x0, y0, x1, y1]` instead of auto-trimming |
| `view_zoom` | viewpoint zoom; 0.5 frames the whole scene, larger fills more of the window |
| `ini_template` | a `.ini` to install into the case when it has none |
| `stills` | times to also save as `i_<t>.png` beside the gif |
| `gif_name` | gif path under `results/`; a `sub/dir/name.gif` keeps cases apart |

Measure the pinned box in two passes: render once with auto-trimming and read
the printed box, take the union over the cases, then pin it in all of them.
Frame size is `x1-x0` by `y1-y0` plus 24 px for the time bar.

## Things that will bite

- **Surface colours must go in the case's own `.smv`.** A side-car `.smv` loaded
  with `LOADSMV` is ignored for colour.
- **`LOADSMV` breaks multi-frame runs.** Changing colours means re-reading the
  `.smv`; after the first `LOADSMV` the data volumes stop reloading and 10 of
  12 frames came out blank. Hence one Smokeview launch per frame.
- **`ZOOM` must come after `SETVIEWPOINT`**, in a second `LOADINIFILE`; before
  it, the viewpoint overwrites it.
- **`RENDERSIZE` does nothing in a batch run.** Set the viewpoint zoom instead
  (`view_zoom`); a tighter zoom makes the scene fill more of the fixed 640x480
  window, so the cropped frames come out larger.
- **PIL's `ImageSequence.Iterator` reuses one buffer.** Collecting it into a list
  leaves N references to the last frame decoded, so every frame reads as the
  final one and a stitch collapses to a single frame. Seek and `.copy()` per
  frame -- `gif_frame.read_frames` does this.
- **The gif and the stills must be written by the renderer.** Output paths used
  to live in the gitignored engine tree, and the stills were copied by hand, so
  the tracked copies went stale while the render itself was correct.
- **`SMOKEPROP` is in m²/kg, order 10³.** Values near 1 are transparent.
  Smokeview's own default is **8700** (`SMOKF3D` in the `.smv`); that draws the
  soot as a near-opaque mass and hides the geometry, so these cases use 300.
- **Smokeview shades surfaces**, so a rendered pixel is the table colour scaled
  — usually ×0.8, up to ×1.05 on lit faces.
- **Smokeview segfaults (exit -11) on the occasional frame.** The renderer
  retries missing frames rather than losing one silently.
