

## Attempt25: nested training-data learning curve (completed 2026-10-25 Pacific)

Eight fresh plain four-state GRUs, one fixed test fold (54 histories /48configurations), validation fold fixed. Training grows48to384configurations. No gates or physical constraints. All8selections frozen before tests; all stopped via validation patience, none hit400epochs. Every manifest file verified:3058files,1491checkpoints,8selected models. CPU/CUDA replay and checkpoint checks passed. VM/jobs/disks empty and temporary grant removed. Original collector completed downloads but bookkeeping failed on timezone-naive BigQuery timestamps; UTC parsing fixed and equivalence tested, no retraining. All outputs preserved in the localDVC mirror; no public upload.

At16seconds ahead during frozen-v1 meaningful activity, more training data helped overall; gains diminished and were not monotonic. Percent error is grouped MAE divided by grouped mean absolute simulation value, not average per-case percentage.

| Training folds | Water error % | Dry fuel error % | Gas release error % | Heating-index error % |
|---|---:|---:|---:|---:|
| 1 | 13.24 | 12.47 | 72.57 | 31.41 |
| 2 | 9.45 | 9.62 | 51.27 | 23.61 |
| 3 | 7.94 | 7.95 | 51.47 | 22.55 |
| 4 | 7.70 | 8.20 | 46.04 | 22.11 |
| 5 | 7.32 | 7.82 | 44.78 | 20.65 |
| 6 | 7.41 | 7.35 | 42.47 | 18.49 |
| 7 | 7.13 | 7.01 | 39.35 | 18.65 |
| 8 | 6.91 | 7.12 | 40.38 | 19.67 |

From1to8folds active MAE decreased47.8%water,42.9%dryfuel,44.4%gas,37.4%heating. Eightfold improvements versus no-change:72.03%,68.10%,75.03%,82.54%. Active MAE at8folds:0.3327kg,2.0089kg,0.10138kg/s,8.8915K; truth denominators4.8144kg,28.2210kg,0.25106kg/s,45.2037K. No-change MAE1.1894kg,6.2981kg,0.40607kg/s,50.9278K. Baseline and truth denominators checked identical at all sizes/all horizons/phases.

Quiet MAE also lower at8than1fold, but remains worse than no-change in all4states. Eightfold quiet MAE0.01487kg,0.13245kg,0.00032245kg/s,1.09444K versus no-change0.000525kg,0.0000621kg,0.00000394kg/s,0.50220K. Tiny quiet gas denominator makes percentage error huge; absolute values are more interpretable. Nonmonotonic quiet drift and invalid water/fuel increases remain.

Full180s gas-total error43.77%to26.03%;peak55.80%to33.09%;median absolute cumulative50/90% timing errors2.58/3.76sto1.99/2.93s. Netwater/fuel-loss MAE1.808/8.623kgto0.914/5.633kg. Late excessgas0.3524to0.1380kg. Eightfold active scenario wins versus no-change32/48water,31/48dryfuel,46/48gas,48/48heating, no ties; medians/p90 and every horizon in scenario-audit.json.

Interpretation: evidence that additional training examples help this recipe, not proof that new simulations will keep improving it indefinitely. One split/order/initialization only; moredata also increasedoptimizerupdates585to4280. Later sizes show diminishing/noisy gains, so no best size is selected usingtest. Data are previously examined simplified conical vegetation simulations, not physical validation. Gas is vegetation fuelrelease not combustionheat; surfaceheatingindex is not storedJ. Existing geometry/source/mesh/char assumptions unchanged.

Run compute estimate $0.5619, measured 0.7950 VMhours, not invoice. Project runtime/shared estimate $28.8079; posted comparison $28.6423, not added together. No further compute or public upload.
