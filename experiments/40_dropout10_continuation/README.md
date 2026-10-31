# Experiment 40: 10% dropout continuation

Continue the selected experiment39 epoch159 complete model/AdamW/RNG checkpoint.
Do not repeat original training. Add Dropout(p=0.1) immediately after the shared
Linear64→64 + SiLU, before BOTH the four-delta and three-gate heads. There are
still25,159 parameters. Masks resample each training forward step; recurrent
memory is not masked. Dropout is disabled for validation/test inference.

Epoch160 onward uses full90-step windows, one origin per history, seven optimizer
updates per epoch at batch256. Preserve rotation0 train1662/validation210/test208,
204test configurations, seed3516, objective and optimizer recipe. Reset patience
at the dropout intervention; minimum190 permits31 dropout epochs, maximum400,
patience30. Retain the parent's best validation checkpoint as eligible selection.
Parent39 epochs160–189 are a different branch and must not enter this curve.

This is an exploratory regularization intervention on historically examined data.
The train/validation gap motivates it but does not prove overfitting is the only
cause or that dropout will help. Full-sequence training has only seven updates per
epoch; compare held-out validation with dropout off. Do not tune against test.

Use three regional ownership-gated Spot T4 queues in Oregon/Iowa/South Carolina.
Only one winner can run optimizer probes/training, after loser cleanup. No queue
allocation deadline or automatic retry. Preserve every completed model, optimizer,
RNG and selection checkpoint. Cloud startup must prove train-mode dropout backward
and bitwise exact next-update replay from epoch159 with restored RNG. No local
optimizer work. Soft/task/VM deadlines13.5/13.75/14h; unfinished epoch is lost.
Paid recovery requires exact diagnosis, verified checkpoint and remaining allowance.

Scientific datasets/models/checkpoints are DVC-controlled and publicly pushed to
the authorized Hugging Face bucket. Financial/controller metadata is private.

## Submission and forward-only validation

Pool01 was submitted once at2026-10-31 00:46 PDT, execution
c82b237f-3cbd-46fa-9db7-2fa615ab7b3a. At00:46 PDT all three regional
Batch queues were SCHEDULED with no VM. Submission is not resumed training.

`validation.json` confirms strict checkpoint compatibility,25,159 parameters,
bitwise equal parent evaluation, stochastic training forwards, and exact forward
replay after RNG restore. No local optimizer was executed. The required cloud
actual-loss backward and optimizer/RNG replay remain pending allocation.

`monitor.py`, `fetch_progress.py`, `audit_startup.py` and the scheduled heartbeat
follow this pool. Every check includes its learning curve; inherited epoch159
train/validation integral errors are4.204650%/5.448502%. Public input and progress
objects were uploaded with hash and anonymous readback verification; private
launch/budget evidence is kept in the separate provenance DVC stage.
