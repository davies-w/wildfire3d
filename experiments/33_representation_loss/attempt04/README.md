# Attempt04: targeted loss repair

Attempt03 showed spatial hot-temperature error~100% even on training, despite6000updates; more updates alone failed. Hypothesis: cold-background pressure and unstable relative-strength gradients compete with missed-fire learning. This is a hypothesis, not a measured causal attribution.

Keep current arm fixed at6000 as reference. Continue loss_only/spatial from6000→12000 on same12train/8validation and deterministic schedule, replacing loss with per-frame hot/bright-region squared encoded errors, downweighted background, smooth log-strength and KL combustion allocation. No architecture change, new simulations or test access. Compare against attempt03 final, not report initial (which is evaluated before checkpoint restoration). Same hard deadlines/checkpoints; new$1.50 allowance in parent central ledger, total$30.60. Expected10–25minutes. All parent data limitations apply.
