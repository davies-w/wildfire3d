# Experiment 39: extend the selected model to long training windows

Continue experiment38 rotation0 from its selected epoch109 **complete** checkpoint,
including model, AdamW optimizer, RNG, history and validation selection state.
Do not train epochs1–109 again. The completed experiment38 and epochs110–139 from
its original 32-step branch remain unchanged; this is a new branch, not its continuation
in chronological epoch order. No new cloud job has been submitted by preparation.

Epochs110–129 use 64-step forecast windows. Epoch130 onward uses full90-step
sequences (91 states, nominal180 seconds). The earlier1/8/16/32 stages are recorded
as lineage only. Minimum absolute epoch160 gives31 full-sequence epochs before
stopping is eligible; maximum remains400, validation patience30. Patience resets
on curriculum transitions and only accumulates after the final transition. Keep
best validation selection across the parent and new stages; an unchanged parent
winner means the new training did not improve selection. Tests remain behind the
selection freeze and are not used for stopping.

At64 steps there are27 stride-one origins per history (44,874 training windows);
at90 steps there is one origin per history (1,662 windows). Batch256 therefore
means176 versus7 optimizer updates per epoch. This changes update frequency and
training exposure as well as the gradient horizon. Full-sequence windows start at
the initial state with zero memory and feed back predictions throughout; shorter
windows retain observed-history initialization and detached prefix memory. The
full90-step gradient graph must pass actual-loss backward and optimizer/RNG replay
on the cloud T4 before training. GPU memory/runtime have not been measured for
these new horizons; no memory-fit or runtime claim is made from preparation.

Architecture remains history8, GRU64, shared64 SiLU, four delta and three gate
heads (25,159 parameters). Preserve the frozen1662/210/208 split,204 test configs,
seed3516, integral objective, gateBCE0.1 and optimizer settings. This remains an
exploratory comparison on historically examined data, not pristine confirmation.

`prepare.py` only reads and copies the checkpoint; it performs no optimizer work.
`dvc repro prepare` builds the immutable candidate input tree. A cloud launcher
must supply `TRAINING_SOFT_SECONDS`, reserve an allowance in the private ledger,
and use a new guarded SpotT4 Workflow with actual-loss/replay startup checks.
No old queue or completed experiment may be resubmitted. Upload scientific
artifacts to the public HF DVC bucket; budgets and credentials remain private.


## Three-region pool and recovery

The user authorized three regional Spot T4 requests: Oregon us-west1-a/b,
Iowa us-central1-a/b/c/f and South Carolina us-east1-b/c/d. One cloud Workflow
creates and supervises all three queues. Every worker waits for an ownership
grant before optimizer probes. The controller chooses the first observed VM,
deletes the losing jobs, verifies jobs/VMs/disks are empty, then grants ownership.
There is no queue allocation deadline. Global GPU quota is one; requests may
contend for it. Each task allows zero automatic retries. Soft/task/VM limits are
13.5/13.75/14 hours; the bootstrap ownership wait is bounded30 minutes.

On confirmed eviction, preserve every completed checkpoint and partial result,
verify hashes and optimizer/RNG state, reconcile allocated cost and empty cleanup,
then prepare a NEW guarded three-region race from the latest completed checkpoint
within the remaining authorized allowance. Never rerun an existing submission or
restart from scratch. A new attempt must adapt prefixes, immutable IDs, transport
hashes and exact resumed-batch replay. Unfinished epochs may be lost. Do not
interpret controller success as Batch training success. Release exact read grants
and reservations only after terminal evidence, measured cost and verified cleanup.

## First submission

Pool01 was submitted once on2026-10-30 at23:34 PDT (2026-10-31T06:34Z),
execution3582eeec-88c2-4e55-9521-a3e38e4edae0. Use `monitor.py` for live state;
submission is not evidence of resumed training. A15-minute scheduled monitor
checks progress and performs the user-authorized verified-checkpoint recovery.
`fetch_progress.py or|ia|sc` and `audit_startup.py or|ia|sc` verify cloud evidence.
`plot_learning_curve.py --output /tmp/longwindow39-learning-curve.png` includes
only parent epochs1–109 plus this branch; never mix in parent epochs110–139.

Scientific input objects are publicly DVC mirrored with per-object Xet hash
verification and anonymous directory readback recorded in
`public-artifact-verification.json`. Private controller/budget evidence goes to
the separate `preserve` stage and must never be included in the public sync.
