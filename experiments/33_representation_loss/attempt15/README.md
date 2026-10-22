# Matched physical heat-release loss diagnostic

48 training configs:12 randomly selected within each truth post-source mean-HRR band <1,1–10,10–100,>=100kW. Selection uses TRAIN truths only. Same prior expanded360 checkpoint/optimizer, same4000-update schedule, physical_low baseline; extra total-HRR absolute error/(truth+10kW), weights0/.02/.1. This floor avoids unbounded weighting of near-zero references; not a claim of calibrated accuracy. Uniform cases on this stratified subset oversamples weak fires in every arm, including control.32 prior development validation configs40trajectories, no pristine test. Check all heat/temperature/radiation/velocity/weak/strong tradeoffs.

Four previously selected height-based animation cases retained, max-y gas-temperature/HRR projections with common scales, not flame geometry. Allarms warmstart; three-frame loss not recurrence. Generic3mwide cones4/6/8/10mabove2m1600particles,.5m24x16x16m180s1500C20s artificialsource,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature. No physicalvalidation.

Reserve3USD fully before submission, cumulative cap75; expected25–45min including88case preprocessing;20minqueue/60mintask/65minVM/90minabsolute;500step uploaded checkpoints, separately reserved recovery only. No laptoptraining/newFDS.24h temporary read development-only prefixes verifiednon-test, removed by lockedcollector.


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
