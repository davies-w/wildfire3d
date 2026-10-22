# Experiment35: identify the surrogate bottleneck before adding losses

Fresh-start fitting diagnostics, not another warm-start loss sweep. One trajectory80 full epochs; eight TRAIN configurations (two randomly selected per training HRR band)20 full epochs. Compare same initial GeometryCNN against an oracle with true instantaneous FDS total HRR as an additional input; its extra input weights start at zero. Separately fit a scalar HRR MLP100 epochs. Oracle performance is a diagnostic upper-information comparison, not a deployable forecast. All32 previously examined validation configurations40trajectories are evaluated after EVERY epoch; full train set for each arm too. Each epoch covers each saved frame exactly once in nonoverlapping three-frame batches, including the final short batch. Average training losses are frame-weighted, all six normalized encoded channels equally weighted. Training8-only std with0.05 floor; no custom regional, temporal, radiation, or total-HRR penalties. AdamW with cosine decay1e-3→1e-5. Training MAE<=0.05 standardized units is a prespecified fitting target, not proof of physical fidelity or convergence. Plot all curves and late slopes, do not automatically call a capped run saturated. Source predictor uses scaled physical HRR MAE; report weak-fire absolute/relative errors. Seed comparison uses8 existing validation replica pairs without fitting to them; not an asserted irreducible floor.

One fully reserved4.50USD cloud attempt, cumulative74.60/100; retain all failed reservations, invoice unknown. No laptop training/newFDS. Expected45–80minutes after allocation;20minqueue,90mintask,95minVM,120minabsolute cloud deadlines. Checkpoint after each epoch and every250updates with model, optimizer, scheduler, RNG, schedule position, and partial epoch aggregate; resume tested by serialization/forward replay on CUDA. Interrupted work is retained; replacement requires separate allowance. No automatic retries. Collector verifies job/VM/disk cleanup and removes exact temporary read grant. Future paid phases are conditional on evidence and remaining budget.

Simulation scope:3m-wide generic conical crowns4/6/8/10m tall above2m,1600weighted particles,0.5m cells over24x16x16m for180s, imposed1500C source20s; no trunks/buildings/embers. Six GAS outputs, no solid-ground temperature. Current model uses four geometry summaries, no explicit evolving fuel state; snapshot predictions not recurrence. Data are development, not pristine tests or physical validation. Existing particle material histories can support later state diagnostics, but that is not claimed by this phase.


Attempt02: separately reserved4.50 replacement for startup404 in attempt01. Five selected training bundles were absent from GCS but retained locally with matching raw SHA256. Restore only those five bundles plus their metadata under this attempt's own prefix; verify all96 inputobjectpaths exist before submission. No scientific/worker/epoch changes. Attempt01 reservation retained; cumulative79.10/100. Original frozen payload unchanged.


Attempt03 separately reserves4.50 after attempt02 completed preprocessing and CUDA checks but failed exact timestamp equality BEFOREtraining. Raw slice audit:8 primary-vs-replica pairs from4 triple-seed configs; maxdifference0.155724s, each91frames, all nearestmatches sameindices. Pairdiagnostic now accepts one-to-one nearestframes<=.2s and records offset; includes temporaljitter, not pure stochasticerrorfloor. Alltraining/validationtargets and optimization unchanged. Reuse five hashverified bundles fromattempt02/restored via narrow temporaryprefixgrant. No automaticretry or recycledbudget. Cumulative83.60/100.

Pre-submission availability check caught further missing originals. Read-only bucket inspection confirms Delete age1 lifecycle rule. No attempt03 workflow existed or compute was submitted. Recovery uses same alreadyreserved4.50 allowance, restoring all48 raw+summary pairs to fresh immutableprefix after localSHA verification;96objects~6GB, narrow24hreadgrantonlynewprefix+overlay. Bucketpolicyunchanged. This avoids ongoing expiration of old inputs.


## Completed diagnostic, 2026-10-22

All four arms completed, with per-epoch training and validation histories. CUDA checks, matched initial predictions and serialization replay passed. Collector verified no remaining jobs, VMs or disks and removed the temporary input grant.

| Arm | Epochs | Final train normalized MAE | Final validation normalized MAE |
|---|---:|---:|---:|
| Source HRR MLP | 100 | 0.41835 | 3.14982 |
| Single trajectory field model | 80 | 0.11824 | 0.44419 |
| Eight trajectory field model | 20 | 0.27755 | 0.41150 |
| Eight trajectory true-HRR oracle | 20 | 0.26404 | 0.37052 |

Source normalization differs from field normalization; do not compare their magnitudes directly. Validation averages replicas within configurations, then configurations equally. Source metrics include the artificial ignition period. The oracle uses true instantaneous FDS HRR and is not deployable.

No field arm reached the prespecified 0.05 training fit target. Oracle information lowered validation normalized MAE by approximately 10% relative to the matched eight-case arm, but improved training fit only approximately 5%. Thus source information helps, but this test does not establish it as the sole bottleneck. Even one trajectory remains imperfectly fitted.

The single-case last five training errors were 0.118321, 0.118226, 0.118209, 0.118227, 0.118243. Eight-case errors declined 0.279158 to 0.277548 over the last five epochs; oracle declined 0.265377 to 0.264040. These are late plateaus under cosine decay to 1e-5, not proof of architectural capacity limits or adequate optimization at a useful learning rate. Source training continued slightly downward while validation slightly worsened near the end.

Next justified diagnostic: isolate optimization on the single trajectory, compare a bounded learning-rate restart against continued low-rate training from identical saved weights and optimizer state, retaining per-epoch full train/validation evaluation. Do not add auxiliary losses or expand data before resolving this fitting question. This follow-up has not yet been launched or reserved.

Evidence: results/analysis.json and data/visuals/*-curves.png, with original epoch JSON and all checkpoints in the DVC cloud_collect output. Cumulative retained reservations remain $83.60 of $100; actual invoice unknown. Existing simulation and validation limitations above still apply.
