# 08 — One ember on a fuel bed, away from any fire

**Question.** Take the flame front away entirely. A single firebrand lands on a
fuel bed — does it ignite it, and after how long?

**Setup.** Three families of deck, all small:

- `ember_test.fds` — an ember landing on a garden fuel bed
- `LS4_ember_ignition.fds` — the minimal single-ember case, derived from NIST's
  `LS4` level-set example
- `bfm_res_test.fds` — the **Boundary Fuel Model** resolution experiment, at
  1.0 / 0.5 / 0.25 m

**What happened — the most useful negative result in the project.** At every
resolution tested, vegetation under the Boundary Fuel Model **burns locally but
the fire never propagates**. Not at 1.0 m, not at 0.5 m, not at 0.25 m. NIST's
own examples that work use **0.05 m** cells, where a 20 × 8 m patch alone is
7.7 million cells — out of reach at property scale.

**Conclusion.** Physics-resolved vegetation combustion is not available at this
scale. The level-set model used everywhere else in this repository is the only
practical option, with the honest trade-off that spread becomes *empirical*
rather than *predicted*. This experiment is why that trade is made explicitly
rather than by omission.

The ember cases themselves confirm the mechanism the literature predicts — a
minimum ember size below which stored heat cannot initiate ignition, and an
ignition delay that grows as the ember shrinks — which is why the ember chain
gets as much attention as the flame front.

**Files.** `make_test_variants.py` generates the resolution variants.
Results: `frame_38.png`.
