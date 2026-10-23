# Experiment35: surrogate fitting diagnostics

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
