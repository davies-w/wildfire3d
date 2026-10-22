# Experiment 33 — spatial representation and loss diagnostic

Submitted as gpu33-pilot01. Synthetic forward/loss/source-removal checks pass. No laptop training or new FDS runs.

Compare 600 additional updates (three consecutive frames each) on 12 existing training configurations and eight separate development-validation configurations:

1. Saved experiment32 snapshot model with original loss.
2. Same saved initialization with balanced hot/background, total-strength, spatial-allocation, radiation, airflow and temporal-difference losses.
3. New spatial density/ignition input model with independent temperature, combustion, radiation and airflow decoders; positive total combustion allocated over a normalized spatial field; revised losses.

All arms share a fixed configuration/time-window schedule. The new architecture starts from scratch; the other arms have prior training. This is a capacity diagnostic, not an equal-total-training architecture comparison. Cases were deliberately stratified by development fire strength and height, not randomly sampled for an IID score. No former fresh-test outputs are ingested. The model remains a snapshot predictor with a temporal-difference loss; it is not recurrent.

Full 180-second histories are evaluated before/after training on each case. Preserve original physical metrics and report percentage errors, weak-burning behavior and cold-background errors separately. Do not decide success from the training objective alone. Improvement on these deliberately selected cases warrants a full-development comparison, not a claim of generalization or physical accuracy. Previously examined test cases cannot serve as a new untouched test.

## Runtime and spending

User approved a cumulative $35 cap; $24.60 prior reservations retained and $1.50 reserved for this pilot ($26.10 total). Pilot allowance $1.50; estimate $0.40–$0.90, approximately 20–45 minutes after provisioning, uncertain until spatial-model throughput is measured. Existing experiment32 reservations remain $24.60 against its $25 cap. Reservation recorded before upload and submission in budget.json.

Prepared Spot L4 workflow: zero automatic retries, 60-minute task limit, 65-minute VM-age limit, 90-minute absolute deadline including queue, 20-minute queue limit and cloud-side deletion. Reserve the full $1.50 before submission, including ancillary/cleanup allowance. Upload checkpoints every100 updates. Worker supports explicit checkpoint restoration and gates training with a CUDA serialization/forward replay check. This checks restoration, not bitwise equality of an additional optimizer step. Interrupted checkpoints must be retained; any replacement needs a separate reservation and new output prefix. launch.py reserves before submission; collect.py preserves outputs and removes the temporary exact-object read grant after terminal cleanup.

## Data limitations

Reuses generic single conical crowns, 3m wide and 4/6/8/10m high above a 2m base, fixed1600 weighted vegetation samples. Domain24×16×16m, uniform0.5m cells,180s. Artificial1500°C particles impose ignition for20s. Wind1/3/5m/s along+X; moisture0.06–0.30 dry basis; loading multipliers0.7/1/1.3. No trunks, buildings or embers. Bare nonflammable ground is heatable in FDS, but solid-ground temperature is not a learned output. Six learned gas fields: temperature, combustion heat-release density, three velocity components and radiation. No claim of real-world validation.

Run setup.py, validate.py and prepare_pilot.py locally; worker.py is CUDA-only. Preprocessing verifies existing raw, deck, checkpoint and density hashes before learning. Frozen input hashes and prepared workflow are under results/ and gpu-workflow.yaml.

## Pilot01 outcome and follow-up

Completed and collected; VM/job/disk cleanup verified and temporary input permission removed. Median post-source validation hot-temperature relative error improved66.77%→57.26% with revised loss, but heat-release63.81%→73.88% and radiation61.61%→68.33% worsened. Current-loss extra updates gave64.14%,73.05%,69.76%. New spatial model after600updates remained at98.80%,93.02%,97.32%, respectively. Do not interpret its low whole-volume error as successful fire prediction: near-ambient predictions can improve that metric while missing fire. Full per-arm/per-case evidence is results/report.json; summarized in results/summary.json.

Attempt02 continues all three arms from their600-update checkpoints to6000 total updates using unchanged models/losses and the same deterministic schedule prefix. This tests whether the fresh model's short training was insufficient before modifying the objective again. Same12train/8validation configurations; no expansion or new FDS. Separate$1.50 reservation, retained pilot01 allowance, cumulative$27.60 if submitted. Actual pilot01 worker learning/evaluation took about162s plus preprocessing/provisioning, much faster than estimate. Allow10–25minutes for attempt02 including provisioning/preprocessing, with the same60min task/65min VM/90min absolute limits. Checkpoint uploads every500updates; the initial600-step checkpoints remain preserved.

Attempt02 was reclaimed by Spot (Batch exit50001) after the current arm uploaded its6000-step checkpoint. No final comparison exists for that attempt. Cleanup/permission removal verified. Attempt03 is a separately reserved$1.50 replacement, retaining previous reservations; resumes current at6000 and the other arms at600, without changing objectives. Cumulative reserved$29.10.

Attempt03 completed; cleanup/permission removal verified. At6000updates median validation temperature/heat-release/radiation errors were66.27/58.99/61.10% current,63.55/74.04/71.95% revised-loss,99.99/431.36/82.26% spatial. Spatial training temperature also99.98%, so there is a capacity/optimization failure rather than just unseen-case generalization. Revised loss reduced whole-volume temperature-rise error415.43→110.00% but did not improve all quantities. These medians are over the deliberately stratified development subset.

Attempt04 targets the loss: per-frame hot/bright squared encoded errors,0.1 background weighting, smooth log-total-strength and KL allocation replace the previous loss. Current6000 model fixed; loss_only/spatial continue6000→12000. Hypothesis of competing background/weak-fire gradients is unproven; compare measured outcomes before expanding data. New$1.50 reservation, cumulative$30.60. All prior results/checkpoints retained. Attempt03 report initial rows evaluate original weights before restoring checkpoints: use final rows across attempts for comparisons.

Attempt04 Spot VM was reclaimed before task startup (exit50001,runDuration0s); no scientific result. Cleanup and permission removal verified. Attempt05 reuses identical checkpoint/loss setup on a regular L4 VM (quota confirmed), with separately reserved$2 full allowance; cumulative$32.60, leaving$2.40. Retain all previous reservations. Same deadlines/checkpoints. This avoids Spot reclamation but does not guarantee capacity/startup or eliminate other failures.

Attempt05 at05:30UTC remained scheduled: us-central1-a resource pool exhausted, no task startup. Existing20min queue deadline and collector remain active; no duplicate job. Forward-only saved-weight diagnostic on first3training cases at30/90s found temperature output clamp fraction0%; this excludes clamp saturation only for those samples. Diagnostic code/results retained.

Attempt05 stopped at the queue deadline after us-central1-a capacity exhaustion; task runtime0s. Cleanup and temporary permission removal verified. Attempt06 is the final separately reserved$2 attempt, regular L4 in supported us-central1-c, identical science and limits. Cumulative$34.60/$35 leaves$0.40, insufficient for another full reserved training attempt. No further paid job should launch under this cap. Finish analysis/report after this attempt, preserving honest failure if capacity remains unavailable.

## Archival update

Latest human approval increased cumulative cap to$75, with archive completion required before further experiments. Reserved$42.60 includes$8 archival allowance; invoice spend unknown. Local download1174files/57,485,004,436bytes is complete; all472rawbundles passedSHA256.91DVCstages pushed to LOCAL mirror with0failures; closure check found5077objects and2imported-input records. Remote submission/collection/resume stages were retrofitted, not originally orchestrated by DVC. Workflow generators/generateddefinitions and local/cloudtraining code are committed. Public HF upload remains blocked pending explicit public-destination approval; no claim of remote archive completion.

Public archive explicitly approved and completed. All5290localmirrorobject paths/sizes matched publicHF (98,529,310,586bytes incl prior model/data artifacts);6anonymoussampledownloadsSHA256matched. All472rawbundles independentlySHA256verified locally, not everyremoteobject re-downloaded. Proof in results/public-archive-verification.json. New attempt07 GPU-only gradient diagnostic launched through actual DVC cloud_submit stage, collection through cloud_collect; cumulative reserved$44.60/$75. No optimizer updates or newFDS.

## Matched loss comparison08

Completed/cleaned with all identical initial weights and metrics verified. Post-source validation median hotT/HRR/radiation/wholevolumeT errors (%): encodedcontrol50.05/69.45/126.83/798.38; radiationdose49.78/65.62/67.71/1065.99; dose+background50.06/67.24/66.91/412.73. Radiation and wholevolumeT improved in all8validationcases with dose+background versus matchedcontrol. Weakfire still badly predicted; not pristine/IIDvalidation. Raw/checkpoints DVC-pushed/publicsynced. See attempt08/results/matched-summary.json for full windows/paired metrics and README for limitations.

Attempt09 submitted: same3GeometryCNN initialcurrent6000 weights/optimizer/schedule2500updates, control08dose_background versus added physical backgroundtemperature MAE/10C weights0.02/0.1. No newFDS. Full2USD reservation retained; cumulative48.60/75. Same cloud deadlines/checkpoints/cleanup and lockedDVCcollector. No laptoptraining.

## Reproducibility audit after09

09 physical-low/high background penalties reduced wholevolume errors but worsened hot-temperature errors; repeated control differs from08. Initial optimizer tensor-sharing was suspected, but checking the complete existing save/reload before training shows it already isolates the state. No optimizer contamination established; that early attribution is withdrawn. Attempt10 strengthens verification with deepcopy/state hashes and a deterministic repeated dose arm. It repeats encodedcontrol/dose_background/physical_low on identical current6000 weights/schedule and checks final repeated weights exactly.

Attempt10 failed before any optimizer update: CUDA trilinear-upsampling backward does not implement deterministic mode. Cleanup/permissions verified; failure reservation retained. Attempt11 separately reserved2USD (cumulative52.60/75) replaces interpolation implementation by equivalent separable matrix products, same real-arithmetic interpolation rule but different floating-point order. Synthetic CPU forward/gradient equivalence passed; mandatory CUDA forward/repeated-backward and finaldose/repeatweights checks precede any reproducibility claim. Same loss/modeldimensions/data; no newFDS.

Attempt11 completed: GPUoperator equivalence/repeatedbackward passed, dose_background/dose_repeat finalweights EXACTmatch, optimizerimmutability verified. Validationmedian hotT/HRR/rad/wholevolumeT% control50.61/67.43/129.87/826.92; dose50.65/65.17/65.74/553.30; physical_low53.64/66.74/64.89/309.71. Radiation improvement reproducible within this environment, temperature tradeoff remains. Allcleanup verified and checkpoints DVC/publicsynced.

Attempt12 submitted frozenevaluation ONLY:32newgeometryvalidationconfigs40trajectories (8replicas) plus12pilottraining; compare current6000 and all3fixed11candidates.24additional configs outside pilot panel, but previously exp32development, not pristine test. Exclude legacy8validation. Configuration-balanced reporting, seedspread, pilot/additional breakdown and4preselected max-yT/HRRprojection animations. No optimization/newFDS. Reserve2.50 cumulative55.10/75, fullclouddeadlines/cleanup. Fixedmodel/data hashes in evaluation-plan.json.

Broader12evaluation completedcleaned. Across32valconfigs40trajectories, config-balanced medianhotT/HRR/rad/wholevolumeT% saved69.56/74.38/69.82/471.79,encoded53.94/75.88/123.98/662.02,dose54.11/74.57/76.21/473.08,physical56.11/72.99/75.61/265.93. Improvements inT extend beyondpilot8 but radiationworse thanoriginalsaved; nooverallwinner. L4 inference median0.22s per180s trajectory excludingpreprocessing/metrics. Fourpreselectedsharedscaleprojection animations underattempt12/data/visuals,notflamegeometry.

Attempt13 frozenfixedloss coveragecomparison submitted: pilot12 vs expanded120trainconfigs (30perheight,108additional fixedrandomwithouttargets), samecurrent6000 weights/optimizer and6000updates, physical_lowloss. All32newgeometryvalconfigs40trajectories; no pristine test,newFDS orlaptoptraining. Larger arm getsfewerepochs underfixedupdates; oldpretrainingalreadyincludedexp32 configs.3USDfullreservation cumulative58.10/75. Samecloudlimits/checkpoints/cleanup, expected25–45min including160casepreprocessing. SelectioncodeandDVCcoverage_inputs retained.

13 completed/cleaned: identicalinitialweights/optimizer/fullhistories verified. Atfixed6000updates,12→120coverage improvesvalidationhotT56.34→46.99%,HRR73.39→67.98%,rad77.76→74.20%,combustionIoU.354→.403;wholevolume228.41→228.44% unchanged,velocity15.28→16.17% worse. Broadertrainfitstilllimited45.65%hotT/54.07%HRR. CheckpointsDVC/publicsynced.14continuesfromsame13expandedcheckpoint:120vs360configs,12kmoreupdates each,fixedloss,32valconfigs40trajectories.4.50fullreserve cumulative62.60/75;100GBdisk90mintask95minVM120minabsolute20minqueue,500updatecheckpoints,expected60–85minafterallocation. No newFDS/laptoptraining; oldpretrainingalreadyincludesexp32data,notfromscratch/freshtest.


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
