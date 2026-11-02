# Five abstract California-interface tree forms

Geometry concepts requested by the user, not a fire experiment or species-calibrated model. Render with `../../.venv/bin/python render.py`. Geometry primitives, stem endpoints/radii and calculated bounds are saved in `data/geometry.json`.

| Type | Total height | Maximum x width | Crown base |
|---|---:|---:|---:|
| Ponderosa pine | 20 m | 7 m | 6 m |
| Coast live oak | 10 m | 12 m | 3 m |
| Blue gum eucalyptus | 24 m | 11 m | 12 m |
| Italian cypress | 12 m | 3 m | 0.8 m |
| Manzanita | 5 m | 6 m | 0.8 m |

Conifer uses three overlapping cones; other crowns use ellipsoids. Crowns are unions: overlap must not multiply eventual fuel loading. Brown cylinders show proposed stems; inclusion in a future FDS thermal/fuel model is not yet specified. Eucalyptus-like form uses separated crown clumps; it does not model bark shedding. No fuel density, moisture, species chemistry, ignition, mesh or embers are assigned. Green shades distinguish forms only, with transparency for geometry inspection. These are proposed sample dimensions, not measurements or species averages.

`five-trees.png` uses per-panel zoom with true within-panel proportions; `five-trees-same-scale.png` uses identical metre limits for size comparison. Individual views are also saved. No FDS or neural training run.
