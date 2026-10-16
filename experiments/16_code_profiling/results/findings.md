# Code profiling results

| Case | Last device/requested simulated s | Wall s | Process CPU s | Mean CPU cores used | Complete |
|---|---:|---:|---:|---:|---|
| hot_a | 30.0/30 | 331.89 | 1193.67 | 3.60 | True |
| hot_coarse | 30.0/30 | 27.22 | 98.43 | 3.62 | True |
| hot_passive | 30.0/30 | 335.69 | 799.31 | 2.38 | True |
| hot_profile | 30.0/30 | 332.28 | 1194.40 | 3.59 | True |
| hot_radiation | 30.0/30 | 322.24 | 1152.96 | 3.58 | True |
| lot_a | 30.0/30 | 345.71 | 1252.11 | 3.62 | True |
| lot_b | 30.0/30 | 339.14 | 1230.34 | 3.63 | True |
| lot_full | 296.50856/600 | 3604.10 | 12468.29 | 3.46 | False |
| lot_profile | 30.0/30 | 340.48 | 1234.22 | 3.62 | True |
| smoke | 8.0/8 | 11.01 | 34.74 | 3.15 | True |

## Paired comparisons

| Candidate vs baseline | CPU speedup | Elapsed speedup | Max wall-device difference (C) | Max roof-device difference (C) |
|---|---:|---:|---:|---:|
| lot_b vs lot_a | 1.018x | 1.019x | 0.000 | 0.000 |
| lot_profile vs lot_a | 1.014x | 1.015x | 0.000 | 0.000 |
| hot_profile vs hot_a | 0.999x | 0.999x | 0.000 | 0.000 |
| hot_passive vs hot_a | 1.493x | 0.989x | 0.000 | 0.000 |
| hot_radiation vs hot_a | 1.035x | 1.030x | 28.990 | 26.396 |
| hot_coarse vs hot_a | 12.127x | 12.191x | 103.309 | 65.798 |

Speedup is baseline divided by candidate; below 1 means slower. Complete 30-second exposures are screening tests, not validation of ignition outcomes over longer exposures. All detailed device errors and profiles are in analysis.json and profiles/.
