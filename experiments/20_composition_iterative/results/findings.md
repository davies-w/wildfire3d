# Experiment 20 results

The frozen graph ensemble correctly classified 19/24 held-out FDS runs. Each comparison ensemble classified 13/24 correctly at the prespecified 0.5 threshold. The test contains 13 ignitions and 11 non-ignitions, verified from raw house boundary data with fds2ascii.

| Model | Parameters per fit | Correct | Brier score (lower is better) | Ignitions detected | Non-ignitions detected |
|---|---:|---:|---:|---:|---:|
| graph | 1182 | 19/24 | 0.179 | 13/13 | 6/11 |
| additive | 1182 | 13/24 | 0.246 | 13/13 | 0/11 |
| simple | 682 | 13/24 | 0.214 | 13/13 | 0/11 |
| ignition_only | 10 | 13/24 | 0.215 | 13/13 | 0/11 |

Each ensemble averages probabilities from five optimization seeds, with epochs selected on validation only. Weights and test predictions were frozen before any confirmation simulations ran. These are not five independent physical datasets. The 24 runs represent four unseen three-crown arrangements, three source powers, and two FDS seeds: only 12 distinct initial-condition combinations. One combination disagrees across its two seeds.

Graph performance varies substantially by optimization seed: accuracy ranges from 54.2% to 87.5%, and Brier score from 0.124 to 0.330. The ensemble has five false positives and no false negatives. In particular, ADG at 1700 kW is predicted around 91% ignition, but neither FDS seed ignites. The aggregate and ten-parameter baselines predict ignition for every test at the fixed 0.5 threshold; their probability scores differ, but their binary predictions do not. No thresholds were retuned on these tests.

Interpretation: this small test provides preliminary evidence that shared graph interactions can help predict some unseen three-crown compositions. It does not establish general physical composability, calibrated ignition probabilities, or the necessity of a graph network. The small sample, correlated seed repeats, optimization instability, and weak extrapolation of the comparison models limit the claim. The graph is trained end-to-end on whole-scene outcomes and surface histories; it is not a separately validated library of physical tree-to-tree solutions.

All scenes share the same toy house, wind, fuel model and 0.5 m mesh. FDS uses an imposed 350 C house ignition criterion. Long-exposure burner-only controls revealed direct-source confounding. Matched shorter exposures demonstrated vegetation-dependent ignition in two scenes, but this does not establish vegetation causality for every training/test positive. No mesh convergence or field validation was performed here.

The acquisition objective is complete: diverse positive/negative development examples were obtained, all four comparisons trained, and frozen predictions evaluated against unseen three-crown simulations. Keep these test outcomes as final evidence; any future tuning requires fresh held-out scenarios.

Cost: $0.355 elapsed-controller compute upper estimate; $0.725 including full ancillary allowances. $1.07 reserved against the $2 authorization. Estimates are not invoice-verified. All cloud VMs, disks and Batch jobs were confirmed removed.

Evidence: results/evaluation.json, results/frozen-weights.json, results/frozen-predictions.json, data/test.json, data/boundary/test, batches/confirmation20/data/cloud-evidence.tar.gz.dvc, and results/cost-summary.json. DVC stages reproduce extraction and evaluation without launching cloud work.
