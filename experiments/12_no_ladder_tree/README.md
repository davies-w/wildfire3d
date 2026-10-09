# 12 — Same fire, no ladder tree

**Question.** Experiment 07 showed the house wall igniting between t = 200 and
248 s. How much of that came from the **ladder tree** — the one whose canopy
sits directly over the fence spur, in contact with it — and how much from the
fence alone?

**Setup.** `wick4.fds`, derived from experiment 07's `wick3c.fds` by removing
exactly two obstructions:

```
&OBST XB=16.0,17.0, 12.5,13.5, 0.0,1.8, SURF_ID='TRUNK'   <- removed
&OBST XB=14.5,17.5, 10.0,16.0, 1.8,6.5, SURF_ID='CANOPY'  <- removed
```

Everything else is identical: 32 × 24 × 12 m, 0.5 m cells, 6 m/s wind, the
fence, the house, the lawn, the wild grass, and the **four wild trees out in
the grass, which stay** — those are at x 2.5–10.5, away from the spur.

`build_wick4.py` derives the deck in code rather than copying it, so the single
difference is explicit and cannot drift.

**Why 300 s and not 350.** In experiment 07 the wall is fully above its
ignition temperature by t = 300 s and gains only ~80 °C in the next 50 s. The
extra 50 s costs about 10 minutes and shows nothing new.

**Expectation, stated before the result.** With the tree gone, the fence spur
still runs unbroken from the west fence to the house wall, so the wall should
still ignite — but later, and the flame reaching it should be weaker. If the
wall ignites at roughly the *same* time, then the tree contributed little and
the fence was doing the work; if it does not ignite at all by 300 s, the tree
was the dominant path.

**Status.** Solving. Started 22:35, expected ~1 hour. `run_wick4.py`.

**Note on embers.** Unlike the recorded experiment 07 run, this case has
`EMBER_GENERATION_HEIGHT = 1.0, 8.0` on the grass surface, so its embers
actually loft. Experiment 07's deck was missing it; see that README.

**Files.**
- `build_wick4.py` — derives `wick4.fds` from `wick3c.fds`
- `run_wick4.py` — native arm64, 4 threads
