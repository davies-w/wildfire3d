# 07 — The house ignites

**Question.** Does the building itself catch? Not "is it hot", but does the wall
cross its ignition temperature and stay there.

**Setup.** `wick3c.fds`. 32 × 24 × 12 m, **0.5 m cells** (73,728 cells), 350 s —
the longest case here, and the one everything else builds towards. Native arm64
build at `OMP_NUM_THREADS=4`, single clean solve, no restart.

Wall temperature is read from the `WALL TEMPERATURE` boundary file over the
house's west face (the x = 18 plane, y 8–16, z 0–3.5 — 136 cells) using
`fds2ascii`.

**Result.**

| t (s) | mean | max | cells above 350 °C |
|---|---|---|---|
| 48 | 23.5 °C | 29.2 °C | 0 / 136 |
| 100 | 30.7 | 51.1 | 0 / 136 |
| 148 | 40.9 | 82.9 | 0 / 136 |
| 200 | 108.0 | **317.6** | 0 / 136 |
| 248 | **589.0** | **1022.2** | **113 / 136** |
| 300 | 975.6 | 1410.4 | 136 / 136 |
| 348 | 1055.7 | 1450.6 | 136 / 136 |

**Yes.** Ignition onset falls **between t = 200 and t = 248 s**; by t = 300 s the
whole wall is above the 350 °C wood ignition threshold, and it stays there. The
rise is not gradual — it is slow, then nearly vertical, which is what a
thermal-feedback ignition looks like.

**Cost.** 350 s of simulated time in **71.0 min**, 16,151 steps, **0.264 s/step**.
The animation is 2 Smokeview launches for 12 frames.

**Files.**
- `build_clean.py` — writes the deck
- `run_clean_arm.py` — solves, native arm64, 4 threads
- `analyse_clean.py` — extracts the wall-temperature history above
- `strip_terrain.py` — **mandatory** post-solve; FDS regenerates the `.smv`
  every solve (see `docs/working-practices.md`)
- `render_wick3c.py` — two-pass render (flame + embers, then burning rate)
- `ign_render.py` + `ign_blend.py` + `make_gif.py` — the ignition-state
  animation: normal colours until a surface passes its own ignition
  temperature, then orange/red

**Results.** `ignition_clean.gif` (12 frames, t = 40–350 s), `i_280.png`.

Note on the animation: two earlier attempts produced a salmon block on the
right and a salmon quad outside the render box. The first was the colour bar,
which exists only in the burning-rate pass. **The second was not** — measuring
the pixels showed the two passes rendering the scene slightly differently just
because a boundary file was loaded. Both are fixed; the second by never painting
background pixels.
