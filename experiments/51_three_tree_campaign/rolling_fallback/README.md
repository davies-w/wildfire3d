# Rolling controller fallback — staged, not deployed

The user requested this fallback while campaign04 continues unchanged. It replaces
an 18-case barrier with at most 18 independent one-case Batch jobs. After a case
finishes **and its job, VM and disks are cleaned up**, its slot can admit the next
case on the next 30-second polling cycle. Slow cases keep their own slots and do
not hold the others. VM provisioning and cleanup still take time: this is not a
persistent 18-worker service and does not promise continuous 100% CPU utilization.

`build.py` emits three Google Workflows templates: `parent.yaml`, `epoch.yaml`,
and `case.yaml`. `__RUN__` is deliberately unbound. No workflow, IAM binding,
reservation, cloud input or solver job has been created for this fallback.
`prepare_rolling.py` packages an explicit future selection into singleton inputs
and renders a new namespace offline. It refuses existing output directories,
duplicate cases, changed source/deck hashes, and recovery bundles. It does not
select unfinished work or assert that an active case is eligible to run again.

The parent owns one sequence of scheduler epochs. Each epoch polls at most 18
case executions and runs at most 60 polling cycles; it hands its compact active
map, input cursor, conservative charge, reservations and checkpoint policy to its
successor. Case jobs continue across this handoff. Outcomes and execution records
are separate immutable objects, so the state does not grow with all 2,000 cases.
The parent has its own poll/time bound. This avoids accumulating the entire
campaign's task polling in one execution.

Each admission reserves a full bounded case allocation in addition to settled
charges and **all active reservations**. A slot and its reservation are released
only by a validated terminal child result with verified cleanup. A lost POST
response, malformed result or failed controller retains uncertainty and requires
an audit; it never triggers a retry. Controller, epoch and case claims use
`ifGenerationMatch=0`, before submission/cleanup. Starting a duplicate epoch
cannot submit another job or delete the original owner's job. All execution and
Batch POSTs are non-retrying; Batch task retries remain zero.

A confirmed Spot50001 failure records an interrupted case and releases its slot
only after cleanup; other never-started cases continue. Its outcome/checkpoint
remains preserved and the interrupted case is not automatically retried. An
ordinary solver/worker failure stops new admission and drains running cases. An unexpected child failure returns
an audit-required state with outstanding reservations rather than claiming that
resources are gone. Scientific acceptance still needs startup/completion, full
180-second devices, exact deck and archive hashes and actual Batch evidence;
a successful scheduler execution alone does not establish it.

Cleanup filters **both VMs and persistent disks by the exact per-case trial
label**, checks returned ownership labels again, and rejects unexpected resource
counts/pages. It does not use the old campaign-wide truncated name prefix.
Google documents allocation-policy labels applying to VMs and persistent disks:
[Batch resource labels](https://docs.cloud.google.com/batch/docs/organize-resources-using-labels).
Actual label propagation, permission scope and empty-resource cleanup still need
verification in the future cloud canary.

Checkpoint adaptation stays remote. Immutable started markers include active
cases in the denominator; failed task history is read once, with a 50-event
bound, using the already approved `batch.tasks.list` capability. Only numeric
50001 events count as Spot evictions, once per case. The global interval only
falls: 480 to 300 seconds at two evictions and 5%, or to 180 at four and 10%.
Both the initial 480 marker and any inherited reduction include the worker's
required run ID. Existing workers retain the 30-second control polling,
900-second clean-stop grace and rejection of forced checkpoint states.

No solver physics changes are included. Fresh case decks and worker code remain
byte-identical; only transport/control namespace strings change. These remain
single generic-fuel, species-inspired vegetation cases on a 0.5 m mesh with an
imposed 0.4 m, 1500 C patch for 20 s, a 180 s target and sparse 36 s 3D outputs.
There is no calibrated species behavior, bark, embers, grass or resolved solid
trunk. The fallback changes scheduling, not the scientific validity of the setup.

## Validation performed

From the repository root:

```
.venv/bin/python experiments/51_three_tree_campaign/rolling_fallback/build.py
.venv/bin/python experiments/51_three_tree_campaign/rolling_fallback/test_pool.py
```

Sixteen offline tests pass. A test interpreter executes the **generated epoch**
against simulated APIs. It checks long-tail refill, 2,000 synthetic cases,
bounded epoch handoff without duplicate submission, allowance exhaustion,
ordinary-failure draining, Spot continuation and policy reduction, and a lost POST acknowledgement.
Additional checks cover claims, isolated cleanup, expression length, exact deck
preservation, bootstrap namespace rewriting, duplicate settlement and refusal to
fresh-start checkpoint recovery. This is an orchestration simulation: no local
FDS, real cloud VM or actual cost measurement is involved. The test interpreter
is not Google's workflow compiler. The templates have not yet been deployed or
cloud-readiness validated.

## Future cutover, only if warranted

1. Let campaign04 finish/stop; inspect actual parent, children and Batch jobs.
   Preserve all outputs/checkpoints, prove all jobs/VMs/disks empty and reconcile
   allocation costs before changing reservations or admitting any continuation.
2. Produce the exact never-started case list from terminal evidence. Exclude
   every attempted/completed case. Package interrupted cases separately from
   their latest verified checkpoints with strict first-new-step/time proof; the
   fresh singleton packager intentionally rejects that path. Retain the old
   terminal-review case separately.
3. Render a unique short namespace and singleton bundles with
   `prepare_rolling.py`. Its index starts `reviewed:false`; fill the audited
   prior count and inherited interval, and review the complete case partition
   before marking it reviewed. Bind admission to only the reconciled original
   allowance. Preserve the protected training hold and total cap.
4. Preserve inputs/source via the existing scoped DVC/HF/Git process. Prepare
   narrowly scoped worker/controller reads and the existing approved roles,
   without extending the original permission expiry.
5. Deploy into the new namespace, validate with Google's compiler, verify source
   and bootstrap equality, then run no-solver readiness for input reads, quota,
   immutable claims, child creation, task listing and per-case inventory access.
   No deployment or launch has been performed by these offline scripts.
6. Run a bounded production canary under the reconciled allowance, verify real
   cleanup labels and scientific output, then allow the rolling queue to advance.
   Never overlap old/new ownership, blindly restart a parent, or re-run paid cases.

The final case selection and funding cannot be frozen while campaign04 is still
making progress. This is a prepared implementation and packaging path, with
cloud acceptance explicitly pending, not a pre-authorized duplicate launch.
