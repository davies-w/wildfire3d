# 02 — Control: the same garden with no lawn

**Question.** Is the house being heated by the fuel fire itself, or by whatever
is burning it? Remove the lawn and see what changes.

**Setup.** `garden_nolawn.fds`. Identical to experiment 01 in every respect
except that the lawn fuel region is deleted. Same 40 × 40 × 12 m, 1 m cells,
120 s.

**What happened.** Unlike 01, the fire is **sustained at ~6 MW** through the run,
and the house wall reaches **555 °C**.

**Conclusion — and it is not the obvious one.** Removing the lawn *increases*
damage to the house. In 01 the lawn burns off and the fire starves; with no
lawn the remaining fuel burns steadily and keeps heating the wall. A
larger-looking fire (01, 138 MW peak) is not the same as a more dangerous one.

This is the control that makes 01 interpretable, and it is the reason later
experiments report *wall temperature* rather than peak HRR: peak HRR is a poor
predictor of whether the building ignites.

**Files.** `run_case.py`. Results: `nolawn_wallT_115.png`.
