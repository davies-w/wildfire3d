# Attempt09: physical-unit background penalty

Matched control is attempt08 dose_background loss, with short-window radiation-excess coefficient0.1 and encoded backgroundtemperature0.5. Two variants add0.02or0.1 times mean absolute background-temperature error divided by10C, masked by truthT<=50C and normalized per frame. Coefficients fixed before validation. All3use same current6000 weights AND optimizer, same3308schedule2500additional updates; control should reproduce08dose_background within GPU numerical variability. This isolates loss sensitivity rather than extra training or data. It tests whether physical-unit error better corrects low-level temperature biases; it does not guarantee prevention of6C floor values or preservation of hot fire. Radiation and heat remain tradeoff metrics.

Prior08dose_background improved radiation and wholevolume temperature for all8developmentvalidation configurations versus encoded control, with little median hot-temperature change. Relative errors still large on weak fire. Full20case histories and original metrics retained; initial weight/prediction equality asserted. Training12andvalidation8 are strength-stratified development, not pristine/IID test; former exp32test examined. No new FDS or laptop training. Three-frame losses not recurrence or fullhistory dose.

Generic3mwidecones4/6/8/10mabove2m,1600weightedparticles,.5m24x16x16mdomain180s,artificial1500C20s ignition,no trunks/buildings/embers; six gasoutputs not solidgroundtemperature. No physicalvalidation.

Reserve2USD before submission within cumulative75; regularL4us-central1-c,expected10–20min,20minqueue60mintask65minVM90minabsolute limits. Checkpoint every500updates, recovery path retained, no automatic paid retry. DVCsubmit/collect and all workflow-generating code preserved.

## Completed results and reproducibility check

Cleanup/permission removal verified. Validation median hotT/HRR/radiation/wholevolumeT%: control49.98/65.49/66.93/568.99; physical_low53.04/64.70/66.13/297.91; physical_high58.05/67.38/69.49/183.16. The physical penalty reduces background error with worse hot-temperature accuracy. Repeated control differs from08dose_background despite identical initial predictions; causes are not established.

Initial optimizer.load_state_dict aliases saved tensors, but the already-existing serialization roundtrip before training breaks sharing. No-training complete-path storage check confirms this. Earlier transient diagnosis of optimizer contamination is withdrawn. Attempt10 adds explicit saved-optimizer immutability checks, independent deepcopy, deterministic settings and a repeated arm. These are stronger verification, not evidence that prior optimizer isolation failed. Original results retained; do not treat tiny improvements as robust until repeated.
