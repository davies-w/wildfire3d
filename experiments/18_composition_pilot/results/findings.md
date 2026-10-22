# Composition pilot findings

Verdict: inconclusive_test_lacks_both_classes.

Positive test cases: 0/12. Qualifying training seeds: 0/5.

| Model | Mean Brier score |
|---|---:|
| graph | 0.00012 |
| additive | 0.00000 |
| simple | 0.12620 |

Four test layouts, one FDS seed, fixed wind/material/moisture; not physical validation or probability calibration.

Raw six-face burning-rate data was extracted with fds2ascii over 0–90 s and cross-checked against device ignition labels. Numerical thresholds: boundary time average >1e-12 kg/m²/s; instantaneous device >1e-9 kg/m²/s.
