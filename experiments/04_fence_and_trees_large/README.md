# 04 — Fence line and six trees in a larger domain

**Question.** Does a fence line, a realistic tree count and more room for the
plume change whether the house is threatened?

**Setup.** `garden_tall.fds` and `wick.fds`. 60 × 60 × 24 m, 1 m cells, 160 s.
Twice the height of the earlier cases, deliberately: a ~150 MW fire in a 12 m
box saturates the domain with soot, and 24 m was raised to fix that.

**What happened.** A **plateau at 50–78 MW** — sustained, and far steeper than
01–03. But the **house stays cool**.

**Conclusion.** More fire does not mean more building heating. The fire is
large and sustained and the house is still not in trouble, because geometry
matters more than total heat release: the fire is not close enough, and hot gas
travels upward rather than sideways at the wall. This is the result that pushed
the two candidate mechanisms apart — radiant heating to the wall versus direct
flame contact — and made the smaller, closer 0.5 m cases (06, 07) the ones worth
pushing.

**Files.** `build_tall.py` writes the deck; `run_tall.py` solves; `render_tall.py`
and `rerender_tall.py` render; `finish_tall.py` / `fix_tall_smoke.py` fix
renderer problems; `make_house_risk.py` + `render_risk.py` produce the
house-facing view; `wick_stage1/2/3.py` build the staged variant.
Results: `c_160.png`.
