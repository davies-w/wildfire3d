# Representation/loss experiment: final assessment

No replacement model is better across the required quantities. Targeted loss improved hot-region temperatures but increased radiation and background errors. Spatial inputs now learn heating, but the spatial model remains worse on validation. Do not expand or deploy this candidate on the strength of one metric.

Median post-source validation errors (%; lower is better), computed across eight development configurations:

| Model | Hot temperature | Heat release | Radiation | Whole-volume temperature rise |
|---|---:|---:|---:|---:|
| Original saved model | 66.8 | 63.8 | 61.6 | 415.4 |
| Current loss,6000 | 66.3 | 59.0 | 61.1 | 554.5 |
| Revised loss v1,6000 | 63.6 | 74.0 | 71.9 | 110.0 |
| Targeted loss v2,12000 | 48.3 | 73.8 | 114.8 | 951.2 |
| Spatial v1,6000 | 100.0 | 431.4 | 82.3 | 101.2 |
| Spatial v2,12000 | 70.2 | 147.2 | 187.6 | 629.8 |

Whole-volume relative errors can be large when the reference temperature rise is near zero. Full/all-time, post-source and late-time metrics, absolute temperature MAE, combustion-region overlap and per-case weak-fire predictions are retained in final-comparison.json and the raw reports.

The loss-only final model fits training hot temperature at39.6% error but validation at48.3%. Spatial final training/validation hot errors are52.8%/70.2%; radiation157.3%/187.6%. This is not sufficient training fit or generalization. Candidate selection on these eight validation cases makes them development data. No new untouched test was performed.

Next steps: diagnose per-output gradient magnitudes on existing training data, calibrate radiation against absolute physical-dose error, and retain explicit background false-heating penalties. First demonstrate reliable fit on a few complete trajectories; then compare equal-initialization/equal-training-budget spatial and summary-input models before full-dataset training. No new FDS data is justified yet.

Twelve training and eight validation cases were deliberately strength-stratified. Old models were warm-started; spatial model started fresh. Temporal-difference loss does not make this recurrent. Generic3m-wide conical crowns4/6/8/10m tall above2m,1600weighted particles,0.5m24×16×16m grid,180s;1500°C artificial20s source;no trunks/buildings/embers. Six gas outputs exclude solid-ground temperature. No physical validation.

All six attempts have verified terminal cleanup and removal of temporary input grants. Two Spot interruptions and one regular-GPU stockout consumed retained reservations. Total cumulative reserved$34.60/$35, including$24.60 prior experiment32; experiment33 reservations$10.00. Reservations are not invoice charges; actual invoice spend is unknown. No further compute authorized within remaining$.40. Checkpoints and immutable inputs retained.

## Later verified development results (attempts11–12)

Deterministic equivalent-interpolation training produced exactly matching repeated-dose weights onL4, with immutable optimizer checks. The earlier optimizer-contamination hypothesis was withdrawn: existing pre-training serialization already broke sharing. No such contamination established.

Broader frozen evaluation (32newgeometryvalidationconfigs,40trajectories; average seeds withinconfiguration) gives postsource medianpercent errors:

| Model | Hot temperature | Heat release | Radiation dose | Whole-volume temperature |
|---|---:|---:|---:|---:|
| Saved current6000 |69.56|74.38|69.82|471.79|
| Encoded refinement |53.94|75.88|123.98|662.02|
| Dose + background |54.11|74.57|76.21|473.08|
| Physical background penalty |56.11|72.99|75.61|265.93|

The physical penalty improves temperature but sacrifices radiation relative to the originalsavedmodel. Not an overallwinner, and errorsremainlarge. Dataarepreviousdevelopment, notfreshindependenttest; legacy8valexcluded. Fourpreselectedanimations showmax-y gasT/HRR projections withsharednonlinearscales, notflamegeometry. L4predictionmedian0.22s/180s trajectory excludespreprocessing/metrics. Attempt13tests12vs120refinementtrainingcoverage atequal6000updates; reserve58.10/75 cumulative, invoiceunknown. Allpriorraw/code/checkpoints retained; no physicalvalidation.
