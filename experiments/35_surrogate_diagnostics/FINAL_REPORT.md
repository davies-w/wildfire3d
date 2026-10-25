# Experiment35: surrogate fitting diagnostics

**Update:** The user authorized a further baseline/occupancy audit and explicit coordinate/time fitting diagnostic after this report. Attempt06 is now submitted; see attempt06/README.md. The conclusions below describe attempts03–05 and are retained. New results will be appended after collection.

## Decision

These diagnostics did not produce a reliable replacement for burning physics. Do not adopt their models over the preserved experiment33 candidates. We established that more cycles and a learning-rate restart can improve aggregate training fit without learning heat release; we also confirmed and removed a local zero-gradient output obstruction, but that change did not repair physical prediction. Stop this diagnostic series rather than spend the remaining allowance on another similar continuation.

## What was measured

Every completed epoch visited all saved frames of the relevant training trajectories exactly once, in shuffled nonoverlapping three-frame batches. Full arm training histories and all32 previously examined validation configurations40trajectories were evaluated after everyepoch. These are snapshot models; batching three frames is not recurrence. Repeated seeds are averaged within configurations before validation aggregation.

Attempt03 started fresh: one trajectory80epochs, eight trajectories20epochs, matched eight-case true-HRR oracle20epochs, source-onlyMLP100epochs. Standardized encoded MAE had equal channel weights, training8 scales floored0.05, and no custom auxiliary penalties. Oracle sees true instantaneous HRR and cannot be deployed as a forecast. Source-only metrics include the imposed ignition period and use different normalization.

| Field diagnostic | Final train normalized MAE | Validation |
|---|---:|---:|
| Single trajectory80epochs | .11824 | .44419 |
| Eight trajectories20epochs | .27755 | .41150 |
| Eight plus true HRR20epochs | .26404 | .37052 |
| Single,80more epochs lowLR | .11681 | .44669 |
| Single,80more epochs LRrestart | .10735 | .49054 |
| Restart lineage,80more epochs clamped | .10159 | .58862 |
| Same start,80more epochs rawHRR | .10263 | .58310 |

The two final arms each have240total single-caseepochs in their lineage (80fresh+80restart+80diagnostic), not merely80. LowLR was a separate branch. No field diagnostic reached the prespecified.05fit target. Oracle improved validation around10% relative to its matched eight-case baseline, but only around5% training; true source information helps without resolving fit. SourceMLP train/validation normalized error ended.41835/3.14982; these numbers cannot be compared directly to field normalization.

## Did we train enough cycles?

We have evidence of diminishing returns and worsening validation on the single-case continuations, not a proof that the architecture is at its best possible solution. Restarting learning rate improved training fit, so the initial low-rate plateau was insufficient evidence of convergence. At the final stages, late training curves are almost flat as learning rate decays; physical HRR fitting remains unsuccessful. The useful conclusion is that more unchanged training is not supported, rather than that every possible optimizer or architecture has converged. One-case validation worsening is also expected specialization and cannot establish generalization limits of a full-data model.

## A confirmed obstruction that was not the whole explanation

GeometryCNN hard-clamps encoded HRR to[0,10] before training loss. Saved restart outputs were negative in every spatial cell at seven nominal training-case times. Negative outputs have zero direct derivative through that clamp. Shared parameters can still change through other channel losses. CPU and actualGPU tests confirmed derivative0 for clamped versus1 for raw HRR, with identical initial physical predictions.

The matched80epoch experiment removed only this training clamp, retaining physical decoding and other transforms. It did not repair burning: training post-source totalHRR error100.00%control versus100.59%raw; hot-temperature error92.17%versus93.18%. Validation HRR median99.98%versus100.74%; mean102.09%versus1386.43%, maximum219.29%versus26122.29%. Weak denominators explain large mean outliers, but even medians show failure. Small whole-volume MAE can conceal failure on sparse hot/burning cells. Sparse-field MAE favoring background remains a hypothesis to test; neither that nor limited representation is established as sole cause.

I should have audited output gradients before interpreting earlier learning-rate plateaus. This diagnostic corrects that omission without claiming the subsequent fix solved the task.

## Next useful work

Before another model sweep, quantify active-cell occupancy and compare constant-zero/ambient baselines under the exact objective, per channel and time window. Then test whether the representation can fit one trajectory with a transparent spatial/time representation and report burning-region errors alongside whole-volume errors. A successful small-data fit should precede expansion. A state-to-state model with explicit evolving fuel/material state is a different experiment requiring a specified state and rollout evaluation; current results do not prove it will work. Do not resume hand-tuned auxiliary-loss sweeps or claim a general burning surrogate from these diagnostics.

## Reproducibility, spend and cleanup

Actual DVC submit/collect/analysis stages, workflow-generating code and frozen hashes are preserved in Git. Rawdata/models/checkpoints/curves are DVC outputs or inputs, published to the explicitly approved publicHuggingFace archive. GitHub branch codex/ignition-surrogate-pilot is pushed; main is not merged. Public archive verification checks all expected paths/sizes and six anonymous SHA256 downloads, not every remote object's fullhash. Original rawbundles were SHAverified locally.

Retained reservations total92.60USD against100USD approval, leaving7.40unreserved. This includes earlier experiments, archival allowance and failed attempts; actual invoiced spend remains unknown. Attempts01/02 failed beforetraining (missing expiredobjects, then replica timestamp assertion); their evidence/reservations remain. Attempts03/04/05 succeeded. Each terminal attempt has empty job/VM/disk verification and exact temporaryreadgrant removal. Attempt05 collector briefly stopped on delayed Batchjob deletion, then collection-only retry succeeded after confirmed absence. No compute retry occurred.

## Scope and limitations

Generic single conical crowns3mwide and4/6/8/10mtall above2m,1600weightedparticles,0.5m mesh in24x16x16m domain for180s. Artificial1500C ignition source20s. No trunks, buildings or embers. Six gasfields include temperature, HRRdensity, threevelocitycomponents and integratedradiationintensity; no solidgroundtemperature. Model uses four geometry summaries, not arbitrary spatial vegetation or evolving fuel state. Validation was already examined development data, not a pristine test or real-world physical validation. Eight primary/replica comparisons across four triple-seed configurations use nearestframes within.2s and include timingjitter, so they are descriptive variability, not a proved irreducible errorfloor.

Evidence: attempt03/04/05 results/analysis.json, attempt04/results/output-clamp-audit.json, attempt05/results/final-summary.json, original per-epoch JSON/checkpoints, and DVC-generated curves.


## Completed coordinate diagnostic (attempt06)

All 40 complete epochs finished: 4,030,464 cell-times per epoch, 246 updates per epoch, 40,582 parameters. CUDA checkpoint replay passed. All 91 frames were evaluated every epoch. Cloud VM, job and disks are absent and the exact temporary input grant was removed.

Matched all-frame post-source comparison (same times and cells): constant ambient/zero-HRR/mean-wind/initial-median-radiation baseline objective 0.110424; coordinate model 0.062210 (43.7% lower). Whole-volume temperature MAE was only 0.1785 C, while hot-region temperature MAE was 61.36 C (baseline 88.91 C). Burning-region HRR MAE was 12.477 kW/m3 versus baseline 12.552, and total-HRR relative L1 error remained 99.43%. Thus the large average-loss improvement did not reconstruct burning faithfully. HRR encoded-channel error was 0.012073 versus baseline 0.011063: worse under that exact channel objective. Only 0.1371% of post-source cells were hotter than 50 C and 0.2588% exceeded 0.01 kW/m3 HRR.

Final full-history objective: training 0.073417, withheld-time 0.077299. From epoch35 to40 these improved by only 0.26% and 0.09%, respectively, under a cosine schedule ending at 1e-5. This establishes flattening under this schedule, not a representation-capacity limit or sufficient optimization under every schedule. Neither reached the earlier 0.05 normalized fitting target, which itself is not a physical-fidelity criterion. Late-time HRR percentage errors have near-zero truth denominators; use the retained absolute errors rather than those percentages as a fidelity measure.

Decision: the requested diagnostic is complete, but the prerequisite successful single-trajectory burning fit has NOT been achieved. Do not expand data or resume auxiliary-loss sweeps on this evidence. No general burning surrogate or state-to-state model has been established. Any next experiment needs a separately specified hypothesis; current results do not prove that adding evolving material state will work.

The nine withheld times are interpolation in the same realization, and historical normalization includes those frames. This is not independent validation. The underlying simulation uses generic 3m-wide conical crowns, 1600 weighted particles, a 0.5m mesh in a 24x16x16m domain and an artificial 1500 C ignition source for20s; no trunks, buildings or embers. Outputs are six gas fields, not solid-ground temperature. The coordinate model has no evolving fuel state or recurrence. Projection images show maximum-through-y gas temperature/HRR, not flame geometry.

All failures and archival allowances remain reserved: cumulative $97.10 of $100, with $2.90 unreserved. Invoice cost is unknown. No further paid job launched.


## Original-physics audit (attempt09)

All472 original runs checked. Real post-ignition burning is present: median21–40s gas-phase HRR4.175MW, declining to1.287kW at60–80s and5.28W at120–180s. Solid oxidation is tracked separately and can persist. Viewer masks match independent raw decoding for all42,952 saved snapshots. Official fds2ascii cross-check passed within0.0005°C. These are short-duration burning simulations, not merely heater cooling, but not sustained burning through180s. Earlier broad “nothing to learn” and “just heating/cooling” characterizations were incorrect. The five late/initial all-cold classification tasks remain trivial.

Physical-cell versus boundary-record distinction matters: at120s physical-cell maxima staybelow50°C, but some excluded index-zero boundary values exceed50°C (maximum62.39°C). No missing physical gas-cell plume was found. Median particle mass reduction48.2% includes moisture/reaction products and cannot be equated to dryfuel burned. See attempt09/README.md for all quantities, limitations and preserved original histories. No new paid work; retained reservations109.10USD of125USD, invoice unknown.


## Continuous U-Net fitting (attempt10, 23 October)

Both fresh conditions-plus-time U-Nets completed 200 epochs with full training and 32 development-validation configurations evaluated every epoch. Both stopped at the epoch cap, not an empirical plateau. Validation-objective selection chose epoch24 for the single-history arm and epoch4 for the eight-history arm; these checkpoints are separate from the final training-fit assessment. No test data were used.

Neither arm demonstrated the prescribed per-case physical fit. Final post-source training hot-temperature / burning-HRR relative L1 errors were 57.55% / 90.66% for the single history and configuration means 27.34% / 86.78% for eight histories. Single-history total gas-HRR relative L1 was100.24%, with200.13kW absolute MAE. The eight-history mean total-HRR percentage was7148.60%, strongly affected by weak-fire denominators; absolute MAE was178.79kW. Use per-case and absolute metrics, not that percentage alone. These are integrals of saved gas HRRPUV, not the separate global solid-oxidation CSV.

Late errors fluctuate: at epochs180/190/200, single training post-source objective was0.5954/0.6073/1.3291; eight was0.4694/0.4408/0.4697. There is no basis to call either converged or interpret the final epoch as a smooth asymptote. No automatic extension, data expansion, architecture change or auxiliary-loss sweep is justified by these results. Variation between different fires cannot alone explain failure to fit one fixed realization. The precise optimization/representation cause remains unresolved.

Both retain the fixed U-Net spatial blocks;14inputs include static conditions and time, with six raw encoded outputs. The single fixed region-balanced standardized MSE changes the prior objective and is not an isolated architecture comparison. This is not recurrence, an evolving fuel-state model, a pristine generalization test, or physical validation. Geometry, resolution, artificial20s source, absent trunks/buildings/embers and six-gas-field limitations remain as described above.

Compute cleanup and temporary-read-permission removal are verified. Checkpoint archival initially stopped because the collector omitted per-epoch NPZ statistics; recovery succeeded. All567 expected checkpoints and all epoch reports/statistics were inventoried with SHA256; the public archive verified37,954 object paths/sizes and six anonymous SHA256 samples. The final supplemental baseline/energy plots are archived alongside the curves. Retained reservations are$116.10 of$125; invoice cost remains unknown. No new paid job has been launched.

Final and validation-selected checkpoints both passed zero complete physical-fit gates:0/1 trainedcase for single and0/8 for eight. Baseline, physical-region, all-channel and gas-energy curves are preserved in attempt10/data/visuals. All outputs are archived; the diagnostic is complete, with no claim that the physical fitting goal was achieved.


## Full-dataset compact-state sequences (attempt13, completed 23 October)

All 520 histories / 480 physical configurations were prepared without exclusions: 47,320 snapshots and 46,800 transitions. Ten grouped rotations used 384 training, 48 validation and 48 test configurations; replicas stayed together. Each configuration was tested once, after all ten validation-selected checkpoints were frozen. These reshuffled simulations were previously examined and are not historically pristine tests.

The residual MLP has 65 inputs (52 evolving summaries plus 13 external/static components), two 128-unit SiLU hidden layers, and 52 next-state outputs; 31,668 parameters. Twenty one-step warmup epochs preceded eight-step backpropagation. Full 180-second autonomous rollouts and one-step metrics were evaluated on training and validation every epoch. Normalization used only each fold's training configurations.

All ten folds stopped by validation patience after 94–196 epochs, selecting epochs 64–166, rather than reaching a budget or epoch cap. Curves show large initial improvement followed by fluctuating, flatter training/validation errors; this meets the declared stopping rule, not proof of physical fidelity or globally sufficient optimization. The equal-configuration held-out rollout normalized MSE was 0.12357, versus mean fold persistence MSE 3.04461 (about 95.9% lower). Persistence keeps the initial state unchanged and is a weak baseline. One-step fold errors were 0.0121–0.0142, while autonomous errors were 0.0944–0.1479: recursive error accumulation remains substantial. This is not a controlled comparison against earlier volume models because outputs, normalization and splits differ.

Physical full-history, configuration-balanced rollout MAEs were 713.60 kW gas heat release, 21.06 m3 HOT volume, and 58.15 C peak gas temperature. All 480 configurations had finite reported aggregate errors. However, negative gas-HRR predictions occupied 36.1–64.2% of evaluated predictions across folds; invalid active plume covariance matrices occupied 51.0–81.1%. These fractions alone do not specify violation magnitude, but negative heat release and covariance matrices that cannot describe a real plume invalidate use as a physical simulator. No silent clipping was applied. The unconstrained model learned useful temporal signal but is not a usable FDS replacement. The data do not establish that these compact summaries are a sufficient Markov state.

All ten learning curves and 52 per-feature curve grids are in attempt13/data/visuals; per-window physical errors, released gas energy, HOT presence, per-case tests and persistence results remain in the archived report. Material mass is not separately dry fuel/water/char; temperature-excess volume is not stored thermal energy in joules. Generic conical crowns and the artificial 1500 C, 20-second source, 0.5 m grid, absence of trunks/buildings/embers and lack of real-world validation remain consequential limitations.

All 1,747 manifest files were hash verified, checkpoints preserved, and DVC outputs uploaded to the approved public Hugging Face archive. Archive verification checked 40,392 remote object paths/sizes and six anonymous SHA256 downloads, not every remote byte. Cloud VM/job/disks are absent and the exact temporary input grant is removed. Source, workflow generators and results are pushed to codex/ignition-surrogate-pilot; main is not merged. Retained reservations total $123.10 of $125; $1.90 is unreserved and actual invoice cost is unknown. No further training launched. This diagnostic is complete; monitoring is paused.


## Three-state material model (attempt15, completed 24 October)

All 520 histories / 480 configurations were used in grouped ten-fold 8/1/1 rotations, with seed replicas kept together. Input [batch,21] comprises four past water/dry-fuel/fuel-gas-release states (12 numbers) plus nine static/forcing quantities. Output [batch,3] is the next water kg, unreacted dry vegetation kg and vegetation fuel-gas release kg/s. The residual MLP has two 64-unit SiLU layers and 5,763 parameters. This predicts neither heat release nor plume geometry. Initial history repeats the initial state; autonomous rollouts never consume future observed states.

All ten validation-selected models were frozen before test evaluation. Nine rotations stopped by validation patience, after 61–225 epochs; one reached the 400-epoch cap without establishing convergence. Selected epochs span31–390. Selection accepts any lower validation objective whereas patience requires a meaningful improvement; this explains fold1 selecting its last epoch despite a patience stop. Full-history and post-warmup plots show substantial early rollout instability, then improvement with fluctuations rather than uniformly flat curves. Missing physical metrics from nonfinite early rollouts appear as gaps; log-scale and epoch21-onward plots supplement the preserved original linear plots. A patience stop does not establish adequate physical fit.

Configuration-balanced held-out MAE across all480 configurations:

| Quantity | One step, observed history | Autonomous180s rollout |
|---|---:|---:|
| Remaining water |0.0195kg|0.7220kg|
| Unreacted dry vegetation |0.1933kg|4.6628kg|
| Vegetation fuel-gas release |0.03057kg/s|0.05221kg/s|

Rollout normalized MSE0.13397 versus1.60679 for unchanged-initial-state persistence is about91.7% lower, but persistence is a weak baseline and this is not physical validation. Integrated released-fuel MAE is6.328kg, peak-release MAE0.6135kg/s and peak-time MAE4.75s. Release MAE is0.2092kg/s during ignition,0.07976kg/s from20–90s, and0.0005375kg/s after90s; late quiet accuracy must not obscure active-period error. The fold-mean active/quiet release MAEs are0.05934/0.0005057kg/s; conditional windows average fold means and need not have identical configuration coverage.

Physical violations prevent treating this as a reliable simulator. Negative water/dry-fuel/release predictions occupy6.27%/1.20%/22.46% of configuration-balanced predicted frames. Average negative magnitude, counting nonnegative values as zero, is0.00797kg/0.00722kg/0.0001226kg/s; global minima are−0.660kg/−3.774kg/−0.007054kg/s. Predicted water and dry mass increase on34.3% and39.8% of transitions (threshold1e-6kg); mean cumulative positive increases are0.276kg and3.685kg per history. Fractions alone exaggerate small violations, but these magnitudes and accumulating rollout errors are material. No silent clipping was applied. Small negative water labels (minimum approximately−0.000490kg) cannot account for the much larger predicted minimum. The evidence establishes learned temporal signal plus substantial recursive error and physical invalidity, not that three states are sufficient, nor that a specific replacement architecture would fix it.

Water/dry-fuel labels are derived by integrated release and an assumed source-audited0.75 fuel-gas yield; char is inert ash by user assumption. Previously examined data were reshuffled with permission, not a historically pristine test. Generic3m-wide conical crowns4/6/8/10m above2m,1600weightedparticles,0.5m grid in24x16x16m, artificial1500C20s ignition and absence of trunks/buildings/embers limit transfer to real trees;48legacy histories retain documented geometry. No new FDS or local training occurred.

All3,629 cloud-manifest files were hash verified and all checkpoints retained. Cloud VM/job/disks are absent and temporary input access removed. Data/models/curves are DVC archived to the approved public Hugging Face bucket; code and workflow generators are pushed on codex/ignition-surrogate-pilot, not merged to main. Archive verification checks all mirror paths/sizes and six anonymous SHA256 downloads, not every remote byte.

Accounting correction supersedes earlier reservation-as-budget-remaining language in this report: historical$123.10 allowances are not spend. This run's measured VM allocation was1.1672hours, yielding an estimated$0.825compute cost; posted billed cost is not yet available. The current whole-project runtime-based estimate is$18.80 including shared costs, versus the last posted comparison$16.55. These overlapping totals must not be added. No further training is launched; this diagnostic is complete.

## Completed matched MLP versus GRU comparison (attempts16–18)

All20 validation-selected models were frozen before held-out testing. All520 histories/480 configurations contributed through grouped ten-fold8/1/1 rotations; replicas remained together. Tests were previously examined and explicitly reshuffled. The continuation restored the actual epoch373 model, optimizer and random-number states on GPU before fitting. No scientific settings changed.

Exactly three evolving outputs: derived remaining water kg, unreacted dry vegetation kg, vegetation fuel-gas release kg/s. Both use21 measured inputs (four three-state frames plus nine known forcing/static values). The GRU has32 internal memory values, not extra physical inputs.

| Forecast horizon | MLP water / dry fuel / release error % | GRU water / dry fuel / release error % |
|---|---|---|
| 2s | 0.76 / 0.97 / 28.39 | 0.75 / 0.76 / 25.97 |
| 8s | 2.61 / 2.57 / 50.18 | 2.40 / 2.39 / 41.78 |
| 16s | 4.63 / 4.39 / 59.48 | 4.18 / 4.12 / 47.43 |
| 32s | 7.24 / 6.67 / 64.44 | 6.43 / 6.42 / 56.04 |
| 90s | 14.32 / 12.93 / near-zero denominator | 12.26 / 13.87 / near-zero denominator |

Equal mean of ten folds; each fold is configuration-balanced. Percentage error = aggregate MAE / aggregate mean absolute true endpoint state, not mean per-case percentage.

Forecasts start at every valid observed origin and feed predictions back thereafter. A90s forecast endpoint lies in the near-inactive latter half of these simulations; release percentage error is misleading because the true mean is approximately0.00000195kg/s. At90s, release MAE is0.000529kg/s MLP versus0.000426kg/s GRU; this is not evidence of90seconds of sustained-burning accuracy.

At16s, GRU reduces error versus matched MLP by9.7%water,6.2%dryfuel,20.3%release; against no-change by62.3%,61.0%,72.1%. Release improves in all ten folds at2/8/16/32s. At90s, GRU water error improves14.4% but dryfuel error worsens7.3% (only2/10folds improve).

Full180s autonomous rollout from the initial state is a separate measure: MLP MAE0.699kgwater/4.150kgdryfuel/0.05562kg/srelease; GRU0.651/3.800/0.04958, improvements6.8%/8.4%/10.9%. Memory helps modestly; it does not remove drift. Negative release occurs in37.5% of GRU rollout outputs, with average negative magnitude0.000161kg/s over all outputs; water negativity and accumulated mass increases also remain. No physical clipping was used.

Seventeen runs stopped by validation patience; three reached400epochs, not demonstrated convergence. Early stopping is evidence about this validation criterion, not proof of an optimization optimum. No new training is launched from these test results.

All1,513 new output files verified, all prior attempt16 checkpoints retained. PublicDVC archive verified54,318 object paths/sizes and six anonymous SHA256 downloads; this is not a complete remote-byte rehash. VM/job/disks empty and exact temporary grant removed. Attempt18 measured-runtime compute estimate$0.3794; whole-project estimate$21.0066, not an invoice. Code and workflow generators are pushed on codex/ignition-surrogate-pilot.

Scope remains derived water/fuel and fuel-gas release, with char treated as inert ash and0.75fuel-gas yield. Generic3m-wide crowns4/6/8/10m above2m,1600weightedparticles,.5m mesh24×16×16m,180s,1500°C artificial20s source, no trunks/buildings/embers;48legacy cases have documented geometry differences. This does not measure heat release or plume physics.


## Thermal and spatial additions — stages19–22

Stage19 audited all520 histories and found a usable surface-heating index, not stored thermal energy: sum current weighted particle mass times(surface temperature minus20°C), divided by initial mass, unitsK. SurfaceTMP_F is not internal temperature; wet material, char and ash contribute. Stage20 compared three states against these same three plus that predicted thermal index. On selected validation full180s rollouts, release MAE improved13.6% and total released-gas amount error24.2%, while water/dryfuel MAE worsened8.3%/2.6%. This was a tradeoff, not a universal gain.

Stage21 extracted three heating-location moments inK m, anchored to the measured initial vegetation mass centroid. These are not heat-flow or plume vectors. A modest validation-only residual association justified one matched experiment; the decision was frozen before using stage20 test scores for model changes.

Stage22 compared scalar4 with spatial7: four history frames plus9known forcing/static values, effective25inputs→4outputs versus37inputs→7outputs. Both used identical initial7047parameter GRUs with32latent memory values; the scalar control masks spatial channels. Added spatial supervision accompanies added information, so this does not isolate a causal mechanism. All520 histories/480physical configurations used the same ten grouped8/1/1rotations, replicas together. All20validation selections froze before test. These reshuffled data were previously examined and are not a pristine new benchmark.

The added spatial moments worsened the original-state predictions. Equal-fold test full180s rollout MAE changed from0.7235→0.7759kgwater(+7.2%),3.6867→4.0554kgdryfuel(+10.0%), and0.04305→0.05077kg/sfuel-gas release(+17.9%). Test next-step MAE also worsened:0.02680→0.03126kg,0.16360→0.22461kg,0.02418→0.03103kg/s. Validation original-state full-rollout errors worsened as well. Therefore retain the simpler scalar representation for this comparison; no further training is launched automatically.

For test full180s rollouts, configuration-balanced total released-gas amount error was27.08% scalar versus35.49% spatial; peak error34.95% versus41.42%; integrated fixed-time absolute release error divided by true released amount42.84% versus50.52%. These are ratios of aggregate errors to aggregate true quantities, not averages of per-case percentages. Amount/peak/timing use positive predicted release, while fixed-time error retains raw predictions. Median absolute timing errors at50%/90% cumulative release were1.55/2.51s versus1.66/2.96s. An optimistic best±10s shift removed16.46%/15.20% of aligned-window error; timing alone does not explain the discrepancy. True-quiet intervals contributed only0.345%/0.583% of absolute release error. These optimistic shifts are descriptive, not deployable corrections.

Spatial model thermal-index MAE was5.93K versus4.61K for scalar. Its location-moment MAEs were1.70/0.98/3.55K m. The scalar model does not predict those three moments; its zero-filled outputs are not fitted spatial results. Negative release occurred in38.58%/35.56% of scalar/spatial rollout outputs, average negative magnitudes0.000139/0.000241kg/s over all outputs. Water negative magnitudes0.01055/0.02055kg and small mass increases remain; no physical clipping was applied. Seventeen models stopped by validation patience; three spatial models reached400epochs, which is not convergence. This result rejects this tested addition under this training scheme, not every possible spatial state.

All20models and tests completed; VM/jobs/disks are empty. All checkpoints are collected and hash-checked. Public archive sync hit HTTP429; archive-only recovery uses sequential25-file batches with pauses, retaining the original failure evidence. Final verification and Git synchronization remain pending. Attempt22 measured-runtime compute estimate is$2.3411 for3.312VMhours; whole-project estimate$25.6710, not an invoice; no active compute allowance remains. Sources: attempt22/data/collected/report.json and attempt22/results/posthoc-{validation,test}.json. No heat-release/plume claim: original three states remain derivedwater,dryfuel,vegetationfuel-gas release, char treated as inert ash, yield0.75. Geometry/source/mesh limitations remain as documented above.
