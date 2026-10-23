# Experiment35 attempt07: ten independent HOT/NOT models

User requested independent models for ten saved times:0,20,40,60,80,100,120,140,160,180seconds. Each has separate weights and AdamW optimizer. NO time input. Architecture, initialization, batch ordering, threshold and loss protocol identical. This replaces the earlier unsubmitted shared time-conditioned proposal; no paid job ran under that proposal.

Frozen existing split:360 primary-seed training configurations and32 validation configurations/40 trajectories. Allframes/seeds of each configuration stay within its split. One epoch visits each of the360training snapshots once,45batches of8; all360train and40validation snapshots evaluated after EVERY epoch. Each model sees one snapshot per configuration at its assigned time. Actual FDS timestamps are within0.2s of nominal bins, one-to-one; actualtimes retained. No label spatialdownsampling:48x32x32cells at0.5m. Original91time labels preserved, only ten selected for this experiment.

Fixed3D U-Net widths8/16/32/64,462673parameters: two3x3convolutions/GroupNorm/SiLU perlevel, learned stride2downsampling, deterministic nearestrepeat upsampling, skipconcatenation. Inputs13channels: four initialfuel-density maps,xyz coordinates and broadcast windspeed/moisture/loading/crownheight/cos-sin ignitionangle. Fuel density scaled by TRAIN maximum only. Ignitionstrength/duration and winddirection are fixed in thisdataset, not additionalvaryinginputs. No targettemperature input. One raw logit for T>50C; thresholdlogit0 fixed. These weightedclassification scores are not calibratedprobabilities.

Class-balanced binarycrossentropy uses frozen TRAIN positive/negative populations separately at each time: halfmeanpositive+halfmeannegative in expectation over fulltrainingepochs. Times withzeroTRAINpositives use ordinary BCE. No auxiliarylosses. Report positiveprecision,recall,F1,IoU,falsepositivefraction,actualhotfraction,balancedBCE and unweightedBCE. Validation replica counts/losses averaged withinconfiguration before aggregation; macroconfigurationmetrics also retained. No-positive recall is null; zero-unionF1/IoU null. Always-NOT baseline explicit. Ten train/validation learningcurves and separate loss curves.

Constantlearningrate3e-4, no schedule-decay-inducedplateau. At least50epochs; every10epochs compare lasttenmean metrics against previous ten on BOTHtrain andvalidation. BalancedBCE change must be <=max(1e-4,1%previous); precision/recall/F1 <=.01absolute. Threeconsecutivechecks required. Undefinedscores stayundefined. Maximum300epochs/model; criterion is descriptive empiricalplateau, not proof of globaloptimum or usefulperformance. FlatpoorF1 is failure, not success. No earlystopping merely for a bestcheckpoint.

CUDA serializationreplay with populatedoptimizer mandatory beforeeachmodel; identicalinitialhash. Checkpoints every500updates/eachepoch include weights,optimizer,RNG,epoch,batchposition,partialaggregates/history/plateaucounts. Independentcompletedmodelreports can be supplied onresume alongside currentmodelcheckpoint; newattempt needs separatefullreservation. No automaticpaidretry. Alltraining cloudGPU; localwork onlydecoding andsyntheticchecks.

Reserve12USD beforeupload/compute:7compute+5ancillarycleanup. Cumulative109.10/125 afterreservation;15.90unreserved,invoiceunknown,allfailedallowancesretained. Estimated3–6hours afterallocation (actualGPUthroughput recorded);20minqueue,6hourtask,6h5minVM,6h30absolute. Worker softdeadline5h40 savespartialcheckpoint. Deadline/300epochcap must be reported as NOT establishedplateau where applicable. Exactoverlay24hreadgrant removed and VM/job/disks checkedempty by lockedcollector.

Package contains compact labels andstaticgeometry from SHAverified localarchivedrawdata; no expiredGCSinputs. DVCpipeline preservesprepare/validate/package/actualsubmit/collect/analysis, checkpoints andper-epochcounts. GitHub source/workflowgenerators andpublicHF DVC archive authorized for35. No newFDS.

HOT gas is not combustion/visibleflames. Generic3mwideconicalcrowns4/6/8/10m above2m,1600weightedparticles,0.5m24x16x16mdomain180s,artificial1500Csource20s,no trunks/buildings/embers. Initialcondition-to-snapshot classifier: no evolvingfuel/materialstate, recurrence orguaranteedtimeconsistency. Validation previouslyexamineddevelopment, notpristinetest/physicalvalidation.

## Completed ten-model run

All ten independent models completed. The active-fire snapshots at20–100s each reached300 epochs without meeting the prescribed plateau rule. The all-cold snapshots at0 and120–180s met the empirical rule at200epochs; their undefined positive recall/F1 is not a perfect positive-class score.

| Time (s) | Epochs | Validation precision | Recall | F1 |
|---|---:|---:|---:|---:|
| 0 | 200 | undefined | undefined | undefined |
| 20 | 300 | 0.6515 | 0.8208 | 0.7264 |
| 40 | 300 | 0.5098 | 0.6383 | 0.5669 |
| 60 | 300 | 0.5280 | 0.8040 | 0.6374 |
| 80 | 300 | 0.3535 | 0.9772 | 0.5192 |
| 100 | 300 | 0.0566 | 1.0000 | 0.1071 |
| 120 | 200 | undefined | undefined | undefined |
| 140 | 200 | undefined | undefined | undefined |
| 160 | 200 | undefined | undefined | undefined |
| 180 | 200 | undefined | undefined | undefined |

Training BCE falls while validation BCE rises at20–60s. This is an observed generalization gap under the loss, despite some F1 improvement. More epochs alone are not justified by these curves. At100s high recall accompanies many false positives and low precision. Fixed threshold0.5 was not tuned on validation.

Final plots are in data/visuals. The separate attempt08 viewer pools recorded cases for visualization only and does not retrain or select checkpoints. All validation/test results remain previously examined development evidence, not physical validation.
