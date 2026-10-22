# Matched physical heat-release loss diagnostic

48 training configs:12 randomly selected within each truth post-source mean-HRR band <1,1–10,10–100,>=100kW. Selection uses TRAIN truths only. Same prior expanded360 checkpoint/optimizer, same4000-update schedule, physical_low baseline; extra total-HRR absolute error/(truth+10kW), weights0/.02/.1. This floor avoids unbounded weighting of near-zero references; not a claim of calibrated accuracy. Uniform cases on this stratified subset oversamples weak fires in every arm, including control.32 prior development validation configs40trajectories, no pristine test. Check all heat/temperature/radiation/velocity/weak/strong tradeoffs.

Four previously selected height-based animation cases retained, max-y gas-temperature/HRR projections with common scales, not flame geometry. Allarms warmstart; three-frame loss not recurrence. Generic3mwide cones4/6/8/10mabove2m1600particles,.5m24x16x16m180s1500C20s artificialsource,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature. No physicalvalidation.

Reserve3USD fully before submission, cumulative cap75; expected25–45min including88case preprocessing;20minqueue/60mintask/65minVM/90minabsolute;500step uploaded checkpoints, separately reserved recovery only. No laptoptraining/newFDS.24h temporary read development-only prefixes verifiednon-test, removed by lockedcollector.
