# Validation burn-shape audit

Frozen validation-selected models, full180s autonomous rollout from the observed initial state; no training or parameter changes. All520 histories/480configurations appear once as validation per architecture across ten rotations. Replicas averaged within configuration. This validation set selected the checkpoints and is not an independent test. This differs from the earlier16s-ahead endpoint metric.

| Measure | MLP | GRU |
|---|---:|---:|
| Total released mass absolute error / mean true total |41.59%|34.71%|
| Peak-rate absolute error / mean true peak |51.22%|41.77%|
| Fixed-time integrated absolute error / mean true total |55.45%|49.29%|
| Median absolute error in time reaching10% of each curve's total |1.13s|1.10s|
| Same,50% |2.10s|1.70s|
| Same,90% |3.24s|2.83s|
| Error reduction allowing at most10s shift |15.31%|15.00%|
| Median magnitude of best shift |2s|2s|
| Excess mass after true99%-released time / mean true total |0.93%|1.15%|
| Quiet share of absolute error |0.40%|0.46%|

Quiet means truth release<=1e-6kg/s, about44.99% of snapshots. Thus quiet periods do not dominate absolute error, although tiny denominators can make quiet-period percentage errors misleading. Remaining amount and peak errors demonstrate that pure timing displacement is not the whole problem. Quantile timings use each curve's own total, separating timing from total amount; correct timing does not imply correct amount.

Total/peak/timing/shift/late-mass diagnostics use positive part of predicted gas release because negative mass release is physically invalid. Raw negative predictions remain saved and included in fixed-time absolute error. No model predictions were altered for feedback. Late release uses true cumulative99% time, not proof of physical burnout. It reports positive excess above the true remaining tail, and does not cancel excess with early cessation elsewhere.

Shift is chosen separately for each validation history using its truth, an optimistic diagnostic and not a usable forecast correction. Candidate shifts are integer seconds within+-10; all compared on a common10..170s grid, with linear interpolation of approximately2s samples. Timing values finer than sampling are interpolated, not higher-resolution physical observations. Timing aggregates are median across configurations after averaging replica signed timing differences; cancellation within replicas is possible. All histories have at least10g total release; none excluded by that timing cutoff.

CPU reconstructed per-fold validation physical MAEs match original GPU summaries within0.00000525 in native units. No optimization was run. Reproducible DVC stage: validation_burn_audit. Full raw per-history metrics and predicted states are in data/validation_burn_audit. Quantity is vegetation fuel-gas release, not heat; same source-derived water/fuel labels and geometry assumptions as the parent comparison.
