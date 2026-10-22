# Current decision after attempt15

Retain attempt14 expanded360 as the best overall candidate from this refinement series. Attempt15 substantially reduces weak-fire overprediction but worsens stronger fires and aggregate validation heat release. No faithful FDS replacement or independent physical validation has been demonstrated. All cloud jobs are finished and cleaned up. Detailed current results are in the final section; earlier sections retain the experimental history.

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

## Training coverage result13

Equal6000refinementupdates on12versus120configurations, fromidenticalweights/optimizer, yieldvalidationmedianhotT56.34→46.99%,HRR73.39→67.98%,radiation77.76→74.20%,wholevolumeT228.41→228.44%. CombustionIoU.354→.403,velocityerror15.28→16.17% worsens. Broadercoveragehelpsfiremetrics,notalloutputs. Moreconfigurationcoverageusesfewerepochs atfixedcompute; modelalreadypretrainedonexp32data. Full32configurationvalidation stilldevelopment,notindependenttest.14testscontinued120versus360at12kmoreupdates, fixedlossandcheckpoint, bounded90mintask withuploadedcheckpoints. Reservations62.60/75,notinvoicespend.


## Completed coverage comparison14

Both arms completed12000 additional updates from identical attempt13 weights/optimizer; all400 initial full-history predictions match. Cleanup verified: no job, VM or disk; temporary input grant removed. Configuration-balanced post-source validation medians (32configs/40trajectories):

| Refinement coverage | Hot temperature error % | Heat-release error % | Radiation-dose error % | Whole-volume temperature-rise error % | Velocity error % | Combustion-region IoU |
|---|---:|---:|---:|---:|---:|---:|
| Continue120 |45.95|63.71|77.56|215.15|15.93|0.377|
| Expand360 |45.98|60.56|65.19|208.36|15.65|0.427|

Broader coverage improves several median metrics, not every configuration: heat-release improves17/32, radiation18/32, whole-volume temperature26/32. Weak burning remains problematic: x32_381 mean heat release0.70kW is predicted11.22kW by expanded360 (continue120:5.56kW); radiation error417% versus270%. This is a useful development candidate, not a faithful replacement for FDS. Training all360 hotT/HRR/radiation errors44.86/51.15/58.58% still show substantial fit limitations. Full histories, seed spread, means and per-case differences retained in attempt14/results/coverage-summary.json.

Same update budget, fewer epochs with360; prior pretraining already used exp32 data. Validation previously examined, not pristine or physical validation. Generic3m-wide conical crowns4/6/8/10m above2m,1600particles,.5m24x16x16m180s, artificial1500C20s source, no trunks/buildings/embers; six gasfields exclude solid-ground temperature. Three-frame loss is not recurrence. Reservations remain62.60/75USD; invoice spend unknown. Next useful work is frozen candidate visualization and targeted weak-fire diagnosis, rather than indiscriminate longer training.


### Strength diagnosis after14

Post-hoc training strata expose a major fit problem:19 configurations with post-source mean FDS heat release below1kW have median FDS0.50kW versus median predicted14.38kW; median relative heat-release error5325%. For74 configurations at1–10kW, medians are2.27 versus22.14kW and relative error609%. For246 configurations above100kW, median heat-release error35.01%. These are separate distribution medians, not paired ratios. Weak-fire radiation errors are also large (595% and465% in the two low-strength strata). Thus this is not only unseen-case generalization or a percentage-denominator artifact; absolute false heat release exists in training. Reproducible DVC strength_diagnosis retains both arms and validation strata. A bounded next loss comparison should penalize weak-case physical heat-release overprediction, with identical initialization and held strong-fire metrics; merely increasing data or updates is not justified. No new paid job submitted for this diagnosis. Public archive verified5485 object paths/sizes plus6 anonymous sample SHA256 downloads; not every remote byte redownloaded.


## Attempt15: weak-fire fit improves, overall candidate rejected

Allthree4000-update arms completed from identical weights/optimizer and identical88initial full-history predictions. CUDA equivalence checks passed; no repeated optimizer arm in this run. Cleanup verified, temporary input grant removed.

Post-source32configuration validation median errors (%):

| Model | Hot temperature | Heat release | Radiation dose | Whole-volume temperature rise |
|---|---:|---:|---:|---:|
| Saved attempt14 expanded360 |45.98|60.56|65.19|208.36|
| Balanced48, unchanged loss |47.76|80.74|74.91|188.99|
| Added strength penalty0.02 |48.11|79.63|76.97|190.87|
| Added strength penalty0.1 |48.87|84.04|76.86|177.82|

On the same12 training configurations below1kW, mean-HRR distribution medians move from12.93kW saved prediction to1.67kW control/1.84low/1.47high, versus0.54kW FDS. This is substantial absolute false-burning reduction, including without the new loss. Validation below1kW (only3configs) goes from2.38kW to0.57/0.64/0.55kW versus0.52kW reference;1–10kW (4configs) also improves. However22strong validation configs (>100kW) suffer: median heat-release relative error38.91% saved versus54.14/55.24/60.45%, and predicted mean-HRR medians729.21kW saved versus338.93/348.87/308.08kW against975.23kW reference. Separate distribution medians are not paired ratios.

Conclusion: weak-fire training fit can improve, but this48case strength-stratified continuation trades away strong-fire output. The added physical strength penalty has no convincing overall benefit over the identically sampled control. This does not isolate resampling from extra updates or reduced configuration diversity; it isolates the added loss within the48case schedule. Retain attempt14 expanded360 as the stronger overall development candidate, not an FDS replacement. Do not spend the remaining allowance on blind longer training. A future useful comparison would retain broad configuration coverage and vary weak-case sampling modestly at equal updates; independent fresh testing remains outstanding.

Four previously selected height-based full-history animations show FDS, saved expanded360 and three refinements. They are maximum-through-y gas temperature and heat-release-density projections, common nonlinear color scales, accelerated playback, not literal flame geometry. Allcases remain generic3mwidecones4/6/8/10mabove2m,1600weightedparticles,.5m24x16x16m180s, artificial1500C20s source, no trunks/buildings/embers; six gasoutputs omit solid-ground temperature. Previous development validation is not a pristine test or physical validation. Three-frame snapshot loss is not recurrence.

Cumulative reservations65.60/75USD, including retained failures/archive;9.40unreserved. Reservations are not actual invoice spend, which remains unknown. No active cloud compute.
