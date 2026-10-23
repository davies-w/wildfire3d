# Experiment35 attempt04: single-trajectory optimization continuation

Compare constant learning rate1e-5 with cosine restart3e-4 to1e-5, each80 additional epochs, from identical attempt03 single epoch80 weights and optimizer. Same loss, training case x32_033_s0, normalization from original8TRAIN configurations, and shuffled nonoverlapping3-frame batch order (seed3501+80+epoch). Each epoch visits all91frames once. All32 development validation configurations40trajectories evaluated EVERYepoch. Not recurrence or a pristine test. No architecture or auxiliary-loss changes. Initial model/optimizer tensor hashes and initial full-history rows must match; learning-rate metadata intentionally differs after the shared restore. Resume preserves each arm's scheduler, RNG, schedule position and aggregate.

Question: did decay to a tiny learning rate prematurely stall fitting? A restart improving fit supports an optimization explanation; failure to improve does not prove a capacity limit. Prespecified training normalized MAE target0.05 remains distinct from physical fidelity. Report all physical outputs and late curves, not just aggregate loss.

Fully reserve4.50USD before upload/compute: cumulative88.10 of100 including prior failures/archive, invoice unknown. No laptop training/newFDS. Estimated40–70minutes;90min task,95minVM,120minabsolute,20minqueue limits. Checkpoint each epoch/every250updates; preserve interruption evidence. No blind retries. Fresh SHAverified copies of all48existing trajectories avoid bucket age1expiry; policy unchanged. Collector verifies job/VM/disks empty and removes exact temporary read grant.

Simulation scope: generic3mwide conical crowns4/6/8/10m above2m,1600weightedparticles,0.5m24x16x16m domain180s, artificial1500C20s source; no trunks/buildings/embers. Six gasfields, not solid ground temperature. Snapshot model uses geometry summaries, not evolving fuel state. No physical validation claim.


## Completed result and output audit

Both80epoch continuations completed. Initial model/optimizer tensor hashes and full initial train/validation rows match exactly. Cleanup confirms no jobs/VMs/disks and temporary grant removed.

Initial train/validation normalized MAE0.118243/0.444186. Constantlowrate finished0.116807/0.446693; restart0.107348/0.490538. Restart improves training approximately9.2% relative to initial, but worsens aggregate validation approximately10.4%. Neither meets0.05. Last five restart training values0.107394,0.107455,0.107427,0.107407,0.107348: nearly flat at decayed learning rate, not proof of a capacity floor.

Physical metrics reveal failure hidden by aggregate improvement. Training post-source HRR error remains approximately100% in both arms. Training hot-temperature error low97.75%, restart95.46%; validation95.55/89.19%. Training radiation-dose error72.90/65.13%; validation662.02/664.57% (configuration-balanced means, unstable for weak denominators). Training whole-volume temperature MAE0.2945/0.2716C, validation1.0991/1.2227C. Background-dominated temperature averages do not imply accurate burning physics.

Inference-only audit at seven nominal times0,10,20,30,60,120,180s on the one TRAINcase shows restarted raw heat-release outputs below zero in every cell at every sampled time. Initial checkpoint is also entirely belowzero at six times and99.9959%belowzero at30s. GeometryCNN clamps encoded HRR to[0,10] BEFORE the training loss. Therefore the direct derivative through that clamp is zero for these negative outputs. Shared features can still move through other channels. This is a demonstrated local gradient obstruction, not proof of sole causality or a successful repair. Radiation outputs were within bounds in these samples. Audit uses nominal times, not a full saved-frame truth comparison.

The earlier focus on optimizer schedules missed this output-path check. Next justified controlled diagnostic is raw encoded HRR training output versus hard-clamped output from identical weights/optimizer; retain nonnegative physical decoding and unchanged MAE/channel scales, compare physical predictions and per-epoch curves. Initial physical predictions can remain identical although the encoded training objective differs. Do not claim adding cycles alone will fix this. Sparse-field MAE can still favor zeros, so removing the clamp may not suffice. No follow-up has yet launched.

Evidence: results/analysis.json, data/visuals/*-curves.png, results/output-clamp-audit.json and its reproducible DVC stage. All checkpoint data retained. Reservations88.10/100USD; actual invoice unknown. Simulation/development-validation limitations above still apply.
