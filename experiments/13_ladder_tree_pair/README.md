# 13 — Ladder tree present versus absent

One pair of decks, identical except for the ladder tree, both carrying lofted
embers, both run for 600 s of fire on the same mesh and the same build.

## Files

| file | what |
|---|---|
| `with_tree.fds` | experiment 7's `wick3c.fds` with `CHID='with_tree'`, `T_END=600` |
| `without_tree.fds` | the same file with the ladder tree's two `&OBST` lines removed |
| `with_tree.json` | render config |
| `without_tree.json` | identical to the above except the case name and output path |
| `view.ini` | the saved `iso_b` viewpoint, installed into each case directory |
| `results/side_by_side.gif` | both animations stitched, frame for frame |
| `results/<case>/ignition_data.gif` | each animation on its own |

`diff with_tree.fds without_tree.fds` reports only the header comment block and
the two ladder-tree lines:

    < &OBST XB=16.0,17.0, 12.5,13.5, 0.0,1.8, SURF_ID='TRUNK', BNDF_OBST=.TRUE. /
    < &OBST XB=14.5,17.5, 10.0,16.0, 1.8,6.5, SURF_ID='CANOPY', BNDF_OBST=.TRUE. /

Both decks carry `EMBER_GENERATION_HEIGHT=1.0, 8.0`. Experiment 7's recorded run
predates that line, so this pair is also the first comparison where both sides
loft embers.

## Result

House west wall, maximum measured temperature, against an ignition temperature
of 350 C:

| t | with tree | without tree |
|---|---|---|
| 200 s | 444 C | 106 C |
| 220 s | 766 C | 112 C |
| 300 s | 1439 C | 135 C |
| 600 s | **1596 C** | **167 C** |

With the tree the house ignites between 180 s and 200 s and burns for the rest
of the run. Without it the wall never reaches a third of its ignition
temperature in ten minutes, and is still climbing at 600 s.

## Reproducing

```bash
python3 scripts/run_fds.py experiments/13_ladder_tree_pair/with_tree.fds \
                           experiments/13_ladder_tree_pair/without_tree.fds \
                           --jobs 2 --threads 4
python3 scripts/strip_terrain.py FDS/cases/with_tree with_tree
python3 scripts/strip_terrain.py FDS/cases/without_tree without_tree
python3 scripts/surface_temp.py experiments/13_ladder_tree_pair/with_tree.json
python3 scripts/surface_temp.py experiments/13_ladder_tree_pair/without_tree.json
python3 scripts/render_animation.py experiments/13_ladder_tree_pair/with_tree.json
python3 scripts/render_animation.py experiments/13_ladder_tree_pair/without_tree.json
python3 scripts/stitch_gifs.py experiments/13_ladder_tree_pair/results/side_by_side.gif \
    experiments/13_ladder_tree_pair/results/with_tree/ignition_data.gif \
    experiments/13_ladder_tree_pair/results/without_tree/ignition_data.gif
```

`strip_terrain.py` must run before the first render: the renderer copies the
`.smv` it finds into `*.smv.orig` and colours every frame from that copy.

The two configs pin the same `crop_box`, measured once from the union of what
each case actually draws. Auto-trimming would give the smokier case a wider box
and the halves would no longer line up, so the stitch would have to scale them.

