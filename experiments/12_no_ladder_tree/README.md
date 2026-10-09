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

**Result — not what I predicted.** The house does **not** catch. Wall
temperature over the same west face (x = 18, y 8–16, z 0–3.5, 136 cells):

| t (s) | exp 12 mean | exp 12 max | exp 12 cells>350 | exp 07 max | exp 07 cells>350 |
|---|---|---|---|---|---|
| 48 | 25.6 | 28.2 | 0 / 136 | 29.2 | 0 / 136 |
| 100 | 45.3 | 55.1 | 0 / 136 | 51.1 | 0 / 136 |
| 148 | 62.8 | 82.3 | 0 / 136 | 82.9 | 0 / 136 |
| 200 | 76.5 | 106.8 | 0 / 136 | **317.6** | 0 / 136 |
| 248 | 85.7 | 124.2 | 0 / 136 | **1022.2** | **113 / 136** |
| 300 | 93.7 | **136.2** | **0 / 136** | **1410.4** | **136 / 136** |

**The ladder tree was the dominant path.** Remove it and the wall peaks at
136 °C at t = 300 s — never within 280 °C of igniting. With it, the wall passes
350 °C between t = 200 and 248 s and is fully involved by t = 300.

The fence spur alone, running unbroken from the west fence to the wall, is not
enough to light the house inside 5 minutes. It is the tree standing in contact
with that spur that does it.

Two caveats, stated plainly:

- The exp 12 wall is still warming when the run ends (124 → 136 °C over the last
  50 s). It might ignite given longer. "Not within 5 minutes" is the claim, not
  "never".
- This is one configuration with one wind direction. It isolates the tree under
  *these* conditions, not in general.

My stated expectation was that the wall would still ignite but later. That was
wrong — it does not ignite at all.

**Cost.** 300 s in **51 min**, faster than the 70 min estimated.

**Status.** Complete. Started 22:35, finished ~23:27.

**Note on embers.** Unlike the recorded experiment 07 run, this case has
`EMBER_GENERATION_HEIGHT = 1.0, 8.0` on the grass surface, so its embers
actually loft. Experiment 07's deck was missing it; see that README.

**Files.**
- `build_wick4.py` — derives `wick4.fds` from `wick3c.fds`
- `run_wick4.py` — native arm64, 4 threads
