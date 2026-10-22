# Attempt14: equal-compute continuation with full new-geometry coverage

Start both arms from the saved13expanded120checkpoint (6000refinementupdates) with identical weights/independentlycopiedoptimizer. Continue120 versus expand360 receive12000additionalupdates with fixedphysical_low loss. All360existing primary-seed newgeometrytrainingconfigs versus reference120;32validationconfigs40trajectories. Legacy40training/8validation excluded. Oneprimaryseedpertrainingconfiguration; validationreplicas averagedwithinconfiguration. Morecoverage means fewerpasses/config atsameupdatebudget. Modelalreadypretrained onexp32; not training unseen trees fromscratch. Previousvalidationexamined; no fresh/pristine/IIDtest claim.

13coverage result at6000updates: hotT56.34→46.99%,HRR73.39→67.98%,rad77.76→74.20%,wholevolume228.41→228.44% for12→120coverage. Broadertraining improvedfiremetrics but notbackground. This justifies boundedcoveragecontinuation, not claims that360willimprove. Evaluate all400trajectories fullhistories, trainreference120/additional240/val32 and weakfires/seedspread. Preserveallmetrics/tradeoffs.

Same deterministicseparable interpolation and optimizerimmutabilitychecks;11repeatedarmverifiedbitwise. No newFDS orlaptoptraining. Generic3mwidecones4/6/8/10mabove2m1600particles,.5m24x16x16m180s1500C20s artificialsource,no trunks/buildings/embers,6gasfieldsnotgroundtemperature;no physicalvalidation.Threeframe lossnotrecurrence/fullhistorydose.

Reserve4.50USD (1.60compute,2.90ancillary/cleanup), cumulative75cap. RegularL4us-central1-c,100GBbootdisk for400decodedcases. Expected60–85min afterallocation includingpreprocess; cloud20minqueue/90mintask/95minVM/120minabsolute limits.500updateuploadedcheckpoints, newprefix/reservationrequiredforinterruptedresume. No blindretry. ExplicitDVCinputs/submit/collect/analysis, archiveallcode/checkpoints/results.

Submission setup recovery: exact800-file IAM list exceeded policy-size limit before any compute submission.36folderORs then exceeded12logicaloperator limit. Verified allselectedgroupmembers non-test, and allx32-development-* groups equal requesteddevelopmentgroups; replaced condition with two development-onlyprefixes plus exactoverlay,24hexpiry. This allows otherdevelopmentartifacts/seedreplicas in those groups, no testgroups/otherprefixes. Collector removes this exactcondition. Existing4.50reservation retained; no duplicatecompute ornewpaidattempt. Firstsubmission succeeded execution53681242-3f67-49dd-a20c-68b079ba854c via explicitDVCrecover_submission stage; originalfailedconditions/verificationproof retained. resume_submission.py refuses after submitted/unknownoutcome.


## Completed coverage comparison14

Both arms completed12000 additional updates from identical attempt13 weights/optimizer; all400 initial full-history predictions match. Cleanup verified: no job, VM or disk; temporary input grant removed. Configuration-balanced post-source validation medians (32configs/40trajectories):

| Refinement coverage | Hot temperature error % | Heat-release error % | Radiation-dose error % | Whole-volume temperature-rise error % | Velocity error % | Combustion-region IoU |
|---|---:|---:|---:|---:|---:|---:|
| Continue120 |45.95|63.71|77.56|215.15|15.93|0.377|
| Expand360 |45.98|60.56|65.19|208.36|15.65|0.427|

Broader coverage improves several median metrics, not every configuration: heat-release improves17/32, radiation18/32, whole-volume temperature26/32. Weak burning remains problematic: x32_381 mean heat release0.70kW is predicted11.22kW by expanded360 (continue120:5.56kW); radiation error417% versus270%. This is a useful development candidate, not a faithful replacement for FDS. Training all360 hotT/HRR/radiation errors44.86/51.15/58.58% still show substantial fit limitations. Full histories, seed spread, means and per-case differences retained in attempt14/results/coverage-summary.json.

Same update budget, fewer epochs with360; prior pretraining already used exp32 data. Validation previously examined, not pristine or physical validation. Generic3m-wide conical crowns4/6/8/10m above2m,1600particles,.5m24x16x16m180s, artificial1500C20s source, no trunks/buildings/embers; six gasfields exclude solid-ground temperature. Three-frame loss is not recurrence. Reservations remain62.60/75USD; invoice spend unknown. Next useful work is frozen candidate visualization and targeted weak-fire diagnosis, rather than indiscriminate longer training.
