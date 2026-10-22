# Domain and resolution comparison

Campaign: complete; ignition bracket relative width: 15.6%; 10% target met: False

| Variant | Paired labels matched | Mean CPU speedup | CPU minutes by endpoint | Fuel mass matched at 1 s |
|---|---:|---:|---:|---|
| mixed | 1/2 | 2.60x | 4.23, 4.13 | True |
| tight | 2/2 | 2.13x | 4.79, 5.41 | True |
| combined | 2/2 | 2.37x | 4.31, 4.85 | True |
| wide | 2/2 | 1.68x | 6.26, 6.64 | True |

| Case | CPU min | CPU speedup | Ignition agrees | Ignition time (reference → case, s) | Max pre-ignition temperature error (°C) |
|---|---:|---:|---|---:|---:|
| compare_08_mixed | 4.23 | 2.52x | False | None → 28.029497 | 290.06 |
| compare_09_mixed | 4.13 | 2.67x | True | 25.010609 → 20.025093 | 185.85 |
| compare_10_tight | 4.79 | 2.23x | True | None → None | 52.00 |
| compare_11_tight | 5.41 | 2.04x | True | 25.010609 → 30.501521 | 148.91 |
| compare_12_combined | 4.31 | 2.48x | True | None → None | 225.22 |
| compare_13_combined | 4.85 | 2.27x | True | 25.010609 → 25.002721 | 74.16 |
| compare_14_wide | 6.26 | 1.71x | True | None → None | 3.71 |
| compare_15_wide | 6.64 | 1.66x | True | 25.010609 → 23.505246 | 97.66 |
| seedcheck_16_full | 10.14 | 1.05x | True | None → None | 18.60 |
| seedcheck_17_full | 10.70 | 1.03x | True | 25.010609 → 26.036724 | 44.13 |

The ignition threshold bracket did not reach its planned 10% relative width; it is reported at the measured width. Raw six-face BNDF burning-rate averages are cross-checked against device ignition labels; see `results/boundary.json` and `analysis.json`.

90-second horizon; a negative means no ignition during this horizon only.
Synthetic house with prescribed 350 C ignition threshold, not a validated house construction.
Particle properties copied from Douglas-fir validation inputs; changed environment and mesh are not themselves validated.
Source strength is a controlled ignition exposure under two crowns, not wildfire intensity inferred from weather.
The t=0 device sample precedes FDS INIT particle creation; fuel-mass matching is evaluated at 1 s.
Raw BNDF burning-rate results are time-window averages over six structure faces; positive samples support ignition, but zero averages cannot rule out brief temperature threshold crossings.
No ember transport in this benchmark; conclusions concern flame/convection/radiation exposure.
Full-domain 0.5 m reference is a numerical comparator, not demonstrated mesh convergence.
