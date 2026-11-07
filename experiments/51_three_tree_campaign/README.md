# Revised three-type campaign

User-authorized design: 2,000 unique one-tree cases, comprising667 pine-inspired,667 eucalyptus-inspired and666 coast-live-oak-inspired cases. Oak crown width is12 or14m and tree height10 or11m, all four combinations. No oak height controls. Pine/eucalyptus retain their25 size combinations each. Old experiments remain immutable.

`prepare.py` selects cases without ranking simulation outcomes. Twenty compact pine/eucalyptus results and two allowed-size oak results are reused by their original deck/proof hashes. The remaining1,978 require new simulations. Oak cases expand environmental/heating combinations within the four approved sizes rather than repeating identical simulations. Wind1–5m/s, moisture6–30%, loading0.7/1/1.3 and mutually exclusive base/crown heating remain in scope. Environment groups are assigned to train/validation/test before new simulations; historical pilots have already been inspected, so holdouts are not historically pristine.

Retain24×16m pine/eucalyptus domains,29×20m oak domains,0.5m cells and180s targets. Z is tree height+6m, with a16m minimum for oak. Generic vegetation and static woody thermal particles are not calibrated species chemistry; no protective bark, embers, grass or resolved solid trunk obstruction. The imposed heating patch is0.4×0.4m at1500°C for20s. Three-dimensional temperatures are saved every36simulated seconds;2D slices every2s. Compact-domain differences remain the previously accepted approximation, not proven equivalence.

## Remote adaptive checkpoint policy

The controller, not a local monitor, polls Batch task status and detects confirmed Spot preemptions via exit code50001 ([Google documentation](https://docs.cloud.google.com/batch/docs/troubleshooting#vm_preemption_50001)). It counts each task once even if an event is repeated; queued tasks do not dilute the denominator. Other failures are not evictions.

Start at480seconds of solver runtime between clean-stop requests. Within a wave, at least two confirmed evictions and a5% eviction rate reduces the interval to300seconds; at least four and a10% rate reduces it to180seconds. Reductions persist across waves, never increase automatically, and never exceed the original wall deadline. These are operational thresholds, not scientifically calibrated optima.

The workflow publishes immutable reduction markers in its unique cloud prefix. Running workers poll them every30seconds, including during a solver segment. If the shorter interval has already elapsed, the worker requests a clean stop promptly. Final state is still saved on exit. A clean stop may take up to900seconds, and upload adds further time: an8-minute request interval is not a guarantee of at most8minutes lost work. Forced stops do not produce accepted checkpoints. A control-read failure retains the last verified interval; it does not manufacture an eviction. Initial control access must pass before FDS startup.

`build_controller.py` generates the adaptation subworkflow and integrates it into the existing controller polling loop before terminal handling. `worker.py` consumes the same remote markers. Six mock-process/policy tests cover live changes, monotonic behavior, threshold boundaries and stop deadlines. No local FDS is run. This policy does not introduce automatic paid retries.

## Execution state

As of 2026-11-04 23:47:48 UTC, campaign04 is terminal after a confirmed Spot preemption in wave011 task2 (case000187). Recovery000136 and 53 fresh cases passed, giving54 successes in this continuation and224 operationally passing cases cumulatively. The original000088 terminal-review case remains excluded. There are1,774 never-started cases and one interrupted case000187; no automatic retry has been submitted.

All606 private campaign04 objects passed generation/MD5/SHA stream verification. All55 VM allocation pairs and four immutable terminal Batch snapshots were audited. Jobs, VMs and disks are independently empty; four exact temporary grants were removed with policy readback verification. All54 successful scientific exports are DVC/HF hash/readback verified. The evicted case has only startup/transport records and **no uploaded restart checkpoint or final archive**; it cannot be represented as resumable saved work. The original failed Batch status remains unchanged.

The rolling fallback has16 offline tests, but no cloud compilation or deployment: automatic approval review rejected deployment as contrary to the prior undeployed-fallback interpretation. An explicit approval question is pending. No new reservation, budget transfer, workflow deployment or solver launch has occurred; allocation reconciliation is prepared privately and the existing reservation remains held. The following sections retain historical launch and failure details.

## Bounded launch authorization

The user reiterated launch after the affordability warning. The new remote campaign is capped separately from protected training funds; it may stop before all2,000 cases. Six new canaries cover all four permitted oak sizes and one case each for pine/eucalyptus. Each later wave contains at most18 cases (72Spot CPUs). Workers retain2h solver/3h task limits; zero automatic retries. Before each wave the workflow checks its remaining compute allowance against a conservative maximum VM-time reservation. Completed wave wall time times task count is charged conservatively, including idle and cleanup time. This deliberately overestimates compute and may stop early; actual allocation reconciliation is required before reusing any remainder. Ancillary costs have a separate private reservation. This is not a guarantee that every planned case will fit.

Production workflow reads its private admission record remotely. Initial control publication and every wave run inside cleanup handling. No local monitor decides checkpoint intervals. A96h scoped read grant covers the72h campaign deadline. Actual cloud readiness and startup proofs, not mock tests alone, are required before claiming execution success.


## Controller step-limit failure and continuation02

Campaign01 stopped at 2026-11-04 09:46 UTC after its repeated task-event scans exceeded the 100,000-step workflow limit. All five launched waves ultimately succeeded: 78 new cases plus 22 reused cases, with full180s exports independently checked. The final wave finished after the last controller snapshot; its actual successful Batch resource was saved before deletion and then pinned in private storage. All779 original objects and all78 allocation start/end pairs were audited; jobs, VMs and disks are empty and the three original grants removed.

Continuation02 selects only the remaining1,900 cases, preserving exact decks, solver image and physical settings. A parent execution carries the original remaining budget and checkpoint interval across separate child executions, one per wave. Child creation and Batch creation are never retried. Each wave claims an immutable object before entering cleanup handling, so duplicate executions cannot submit or delete another execution's job. The parent records child identities and outcomes. A parent failure does not imply its child stopped: audit the child and resources before any continuation.

Healthy task histories are no longer scanned. Failed-task histories are scanned only when the failed count increases above the threshold, with bounded task/event counts. Each child has at most375 job polls, bounded cleanup loops and a single quota check. Unexpected history size fails closed for diagnosis. The remote480/300/180-second adaptation remains, with900-second clean-stop grace and no solver retries. A read-only child dry run checks invocation permissions and frozen-wave arguments before launch. These controls fix orchestration; they do not establish additional physical validation or guarantee that the full remaining campaign fits the protected allowance.

Before the explicit permission approval, continuation02 was deployed but not submitted. Cloud readiness passed input reads, immutable writes, quota and task-list checks, then stopped at child-execution permission. Workflows does not support the resource.name IAM condition used to scope that permission to one workflow. Replacing it with an expiring project-scoped create/get-only custom role was rejected by automatic approval review. `fix_child_permission02.py` is prepared with an explicit approval guard and has NOT been executed. A project-scoped grant would permit the watchdog to start/read any workflow in this project during its expiry period; it adds no deploy, IAM-edit, or direct compute permissions. This required explicit user approval before launch, subsequently received below.

The user explicitly approved the temporary project-scoped execution create/get permission on November4. The guarded permission correction was applied, expiring November8 at09:16PST and to be removed on campaign closure. No deploy, IAM-edit or direct compute permissions were added.

Continuation02 was submitted ONCE at2026-11-04 17:47:41UTC (09:47PST), parent execution338ce056-c12c-45a6-a08c-8c564292dab3. Actual readiness and child dry run succeeded after IAM propagation. The first child created wave005 with18 tasks; its initial Batch state is SCHEDULED, not yet evidence of solver startup or completion. Inputs, exact deployed source, Git and budget checks passed before submission. Do not rerun preparation, packaging, deployment or launch after this intent.

Campaign02 stopped during its first wave after17 workers passed and case000088 reported failure. Its verified final archive shows a clean-stop request coinciding with physical180s, followed by an unnecessary restart rejected by FDS with ERROR(1051), “RESTART initial time equals T_END.” This is a worker completion/stop race, not evidence of numerical instability. The original FAILED Batch/completion status remains unchanged. Its full-time scientific outputs require separate review; do not silently count this case as operationally passed or blindly rerun it. The controller stopped further waves and removed current resources; terminal archive/allocation audits are in progress before any continuation.

Campaign02 terminal closure is complete: all268 private objects were pinned and streamed through MD5/SHA verification, all18 allocation pairs reconciled, resources empty, and four exact grants removed. Seventeen passing outputs are collected and DVC recorded. Separate review of000088 confirms finite device/HRR series through180s, initial-mass probe acceptance, and a clean terminal checkpoint atstep1920/time180; its operational FAILED status is unchanged. It is excluded from new submissions pending explicitly qualified scientific acceptance, not silently counted as passing.

Continuation03 is prepared for1,882 never-started cases only. `worker03.py` uses `completion_check03.py` against the current invocation's stdout. It accepts a clean-stop marker only after strictly increasing progress reaching180s, with finite full-target device time, zero exit code and no forced termination or error marker. This prevents restarting atT_END. Eight regressions use actual archived clean-stop and normal-completion logs plus negative cases. No local FDS or new physics ran. The package excludes96 prior attempts (95 passing and one terminal case under review), plus22 earlier reused cases. A fully successful continuation would yield1,999 operationally passing cases plus the reviewed case; the final target is not claimed complete automatically. Any new project-wide execution grant keeps the original user-approved November8 expiry.

Continuation03 was submitted ONCE at2026-11-04 18:40:25UTC (10:40PST), parent executionad096283-5176-4360-81a3-56a88fbeb53d. Actual cloud readiness, child dry run, full1,882-deck validation, all deployed-source checks, source Git, and108 scientific input remote hashes/readback passed before submission. This resumes only never-started cases under the original remaining allowance, with training funds protected and000088 still excluded for separate review. Never rerun03 preparation, packaging, deployment or launch after submission intent.

Campaign03 stopped after a confirmed Spot preemption in wave008 task5 (case000136). Waves006/007 each succeeded18 tasks; the final immutable wave008 Batch snapshot records17 successes and one failure. The saved per-task response identifies the single permanent failure as task5 with exit50001. Because this is a fixed18-task job with zero retries, the final17-success/one-failure counts establish success of all other task IDs, including four still running at the earlier per-task snapshot. Collection excludes000136 and still requires exact deck hashes, passing startup/completion, full180s result/devices and archive hashes for each accepted case. The original wave FAILED status remains unchanged. The interrupted case has a preserved checkpoint atstep1800/time121.56627s; all18 declared inner-file hashes pass, but cloud restore and advancing progress remain untested for this checkpoint.

After explicit user approval, campaign03 closure completed: all573 private objects and54 allocation pairs were audited, jobs/VMs/disks were independently empty, and its four exact temporary grants were removed. The audited original remainder is reserved for a unique continuation04; no extra allowance or training funds were used. All53 passing scientific exports are DVC recorded and remotely hash/readback verified. Continuation04 has not been submitted.

Continuation04 starts with one checkpoint-only recovery of000136 fromstep1800/time121.56627s, then1,828 never-started cases in102 waves. The recovery must hash-verify restored files and demonstrate a strictly advancing first step/time before startup acceptance. It uses the same terminal completion checker, dynamic480/300/180-second remote checkpoint policy,900-second stop grace, four threads, exact deck and binary. No local FDS ran. Four restore tests and eight completion regressions pass; the full1,829-input check preserves original decks and excludes completed cases. A successful run would yield1,999 operationally passing cases plus000088 still separately reviewed. The original remaining allowance and protected training funds still bound admission.

Continuation04 submitted ONCE at 2026-11-04T22:45:24.949914310Z, parent execution8d1e96b4-44b1-4a7f-b1f9-0a1c240ceaa0. Actual readiness and child dry run succeeded, all1,829 input decks validated, all106 input objects remotely hash/readback verified, and deployed-source/Git/budget checks passed before submission. First wave008 is checkpoint-only recovery; remaining102 waves contain never-started cases. No further preparation, packaging, deployment or launch may run after this intent.

### Prepared rolling fallback (2026-11-04)

At the user's request, [rolling_fallback/README.md](rolling_fallback/README.md)
contains an undeployed replacement for the wave barrier. It admits one case per
free slot, at most 18, after per-case cleanup; a long case does not delay other
slots. Sixteen offline tests exercise the generated scheduler, including
long-tail refill, bounded epoch handoffs, budget exhaustion, duplicate protection
and Spot policy accounting. Campaign04 is now terminal; this fallback is still undeployed. Google's
compiler/readiness and a real isolated-cleanup canary are still required at a
future audited cutover; no new solver launch or allowance was created.


### Approved rolling continuation05 — preparation

The user approved rolling continuation after campaign04’s terminal audit. Campaign04 is closed, all four temporary grants retired, and all 54 successful scientific exports preserved. The audited original remainder alone funds the continuation; the protected training allocation is unchanged.

The unique t51r05 controller selects 1,774 never-started cases plus one diagnosed fresh replacement of Spot-evicted case000187. That failed attempt had no checkpoint, so its replacement starts from zero; it is not a resume. The 224 accepted cases and old000088 terminal review are excluded. Success of all 1,775 would establish 1,999 operational completions, with000088 still requiring separate qualified review. Physics, decks and solver binary remain unchanged.

All four rolling workflows compile on Google Workflows. Actual case/epoch/parent dry runs passed after correcting JSON content-type metadata, without changing input bytes. One production case is gated before bulk admission. Independent Batch success, full180-second scientific evidence, archive integrity and exact-resource cleanup must pass before a remotely stored gate permits more cases. Thereafter up to18 singleton jobs refill available slots without waiting for the slowest case. A later confirmed Spot preemption records the interrupted case and permits other never-started cases to proceed; no automatic retry is enabled.

Production submitted once at 2026-11-05T01:31:45.170871233Z; execution `27eeb7ab-3cc6-40fb-a095-53146a40f9ad`. Actual first Batch job `t51r05-c0` is queued. The initial queued state has since advanced: independent canary verification passed and the rolling admission gate was released.


Rolling05 production canary passed independent full180-second device/result checks, original-deck hashing, archive generation/MD5/SHA verification, actual singleton Batch success and empty exact-case resources. The continuous watcher released admission automatically. At the next actual inventory, the parent remained active with18 distinct singleton jobs RUNNING and18Spot VMs. This establishes cloud execution of the rolling controller; observed slot refill and longer scheduler handoff remain to be verified as cases finish. There are now225 accepted cases including the diagnosed000187 replacement; no old failure record was changed.


Rolling refill is now observed in actual cloud state: later singleton cases through index36 were running while earlier indices4 and13 remained running. The first production scheduler epoch finished successfully and handed18 active child executions to its successor (cursor37, no interrupted cases or audit-required flag). This confirms both long-tail refill and the first bounded execution handoff in production. An additional bounded group of18 scientific exports passed full180-second device/result, original-deck, archive and immutable Batch-success checks; controller counters alone are not used as scientific acceptance.


### Rolling05 admission stop: Batch creation HTTP502

At2026-11-05T02:31:20Z the parent returned `target_complete:false` and `audit_required:true`, despite its outer Google execution state being `SUCCEEDED`. The failed child at index71 encountered HTTP502 specifically at the Batch `create` step. Its creation POST was not retried. This is an ambiguous infrastructure submission failure, not evidence of numerical solver failure. Other children continued independently; active resources and reservations must remain intact until those children finish and the terminal allocation audit proves cleanup. No new continuation has been submitted. Case71’s execution/resource eligibility remains unresolved until that audit; absence of a completion record alone does not prove it never started.


Rolling05 is fully closed after generation/MD5/SHA verification of6,280 private objects,71 complete VM allocation pairs and71 immutable successful singleton Batch snapshots. All71 scientific exports are DVC/HF verified, giving295 operationally accepted cases. No VM allocation, Batch snapshot or case output was observed for index71/tree51_000273_baseline; its ambiguous creation response is retained unchanged and a new unique attempt is separately justified by that terminal audit. All four exact temporary grants were retired and only the audited original remainder was reserved for continuation06. No budget increase or training allocation use occurred.

Continuation06 preparation selects1,703 never-submitted cases plus the audited unallocated000273 case, excludes295accepted and the old000088 review, and keeps the same physics/decks/binary. It uses a new namespace and another independently verified first-case gate. Continuation06 was submitted once at 2026-11-05T03:16:19.534019159Z (execution `0e581545-12c7-4369-a78c-3d0dd00d56f6`). The first case subsequently passed full180-second scientific, archive and cleanup verification, and the continuous watcher released the rolling gate.


Continuation06 has demonstrated actual rolling refill: cases19–21 entered while earlier cases remained running. Canary000273 is independently accepted, bringing the verified operational total to296 before subsequent case collection. The controller remains active; later completion records still require the same archive/device/Batch checks before acceptance.

Completed Attempt 6 exports may have their local `solve/` files evicted after
matching their full SHA256 and sizes to a dedicated DVC/HF plan with successful
remote-hash and anonymous-manifest verification. `evict_preserved06.py` handles
one bounded group under the preservation lock and retains all local proof files,
private receipts, DVC hashes, and remote originals. Incomplete cases are excluded.
These partially populated local output directories must not be recommitted to
DVC: restore the exact output records using the scoped procedure in
`docs/storage.md` when the bulk files are needed again.

### Experiment 51, Attempt 6: monitoring-write failure

The controller stopped new admissions after child171 encountered a connection
failure in `record_state`, while uploading a job-status snapshot. Its generic
exception handler cleaned up that case. This is a controller-design defect:
a monitoring-write failure should not terminate running computation. The
parent's outer `SUCCEEDED` status contains `target_complete:false`,
`stopped:true`, and `audit_required:true`; it is not experiment completion.
Remaining children must finish and their actual outputs/resources be audited
before a corrected unique continuation. No solver failure is established by
this connection error, and no lost case is automatically retried.

The offline successor template now retries only immutable monitoring-snapshot
uploads. If those retries are exhausted, it resumes polling within the existing
task deadline, without deleting the running job; terminal cleanup still requires
a saved snapshot. Job and execution creation POSTs remain non-retrying. Eighteen
offline tests pass; cloud compilation and readiness remain required before use.

### Experiment 51, Attempt 7: continuous restart

The original Attempt 7 parent admitted 19 cases and stopped after two admission
failures: index9 encountered a missing regional `quotas` field; index15 received
HTTP502 at Batch creation. Seventeen cases passed independent full180-second,
original-deck, finite-device, archive and singleton Batch-success verification;
all17 exports are DVC/HF preserved with remote hash and anonymous manifest
readback. Together with468 earlier accepted cases,485 are now accepted. No
allocation was observed for indices9/15 in the bounded allocation audit; they
remain excluded and are not silently retried or accepted.

The repaired case workflow waits for missing/unavailable quota within a bounded
window. A transient Batch creation error reconciles the original job ID by GET,
without retrying its creation POST. If that job remains absent and exact resource
inventory is empty, it defers that case, retains the full conservative admission
charge and continues other cases. A quota wait that expires likewise defers the
case. Deferred cases still need later review; this is not a claim that every
requested case will complete. Genuine solver failures and unexpected errors
retain the existing stop/drain behavior.

The one-time continuation in `continuation-record07.json` starts at index19,
retains charges for the two excluded admissions, and reuses the frozen original
inputs. It has no first-case gate or laptop-dependent admission step. At most18
singleton jobs may be active, with original compute limits and exact cleanup.
Google compiled and read back all three repaired controls; no-solver executions
passed. The existing18 admission/budget tests passed. These checks do not prove
that every future service failure can recover; the live continuation remains
subject to monitoring and scientific verification. The earlier parent result and
all prior job identities are retained unchanged.

Progress reporting must include pinned failed-task and deferred-admission outcomes,
not only live Batch jobs (completed/failed jobs are cleaned up). The inspector now
caches these immutable records too. Run `summarize_progress07.py` after inspection
and collection: it counts local scientific proofs, confirms Spot exit50001 against
task evidence, and lists deferrals separately. Earlier reports that repeated only
the two original admission failures omitted later interruptions; use the current
summary instead. Interrupted checkpoints remain in private remote storage and
must be reviewed before any proposed recovery; interruption is never acceptance.

The first continuous restart stopped admitting cases when two Batch jobs (indices
514 and 515) failed with zero reported task runtime and the task status check
could not classify them. Both had VM allocations. Neither produced scientific
output. After the remaining jobs finished, 961 of 2,000 cases had verified
results and backups. No jobs, VMs or disks remained, and the allocation review
paired 519 VM starts and deletions. The second continuation starts at index
522 and skips every previously submitted index. A future failed job with zero
reported runtime, no observed task start, no task groups, and an empty task
list can be deferred after its evidence is saved and cleanup is verified. Its
full reservation is retained. Other unexpected task responses still stop
admission for review. The budget can stop the workflow before all cases finish.

The second continuation finished with all its jobs drained. At that point,
1,018 of 2,000 cases had verified scientific results and backups. The scheduler
could not reserve another job against its running estimate. Checking 579 VM
allocation pairs and the empty job, VM and disk inventories established room
for one concurrent job under the existing allowance. The third continuation
starts at the first untouched index, 582, and retains all five unresolved
admission reservations. Its remaining queue is subject to the same budget limit.

### Experiment 51, Attempt 7 ended at its budget limit

**1,022 of 2,000 cases are verified complete and backed up.** Earlier attempts
contributed 468 cases and Attempt 7 contributed 554. Each accepted Attempt 7
case reached 180 simulated seconds, passed the archived original-deck and
device checks, had a successful Batch task, and has a verified scientific backup.

Of the remaining 978 cases, 945 were never submitted, 27 were interrupted on
Spot VMs, 3 were deferred, 2 jobs failed with zero recorded task runtime, and
1 older case remains under scientific review. Twenty-two of the interrupted
cases retain checkpoint manifests. Their restartability has not been tested.

The third continuation drained. The final allocation review covered 583 VM
start/delete pairs. With the five unresolved admission reservations retained,
the existing compute allowance cannot reserve another job. All jobs, VMs and
disks were gone at closure, and the four temporary grants were removed and
checked. Private raw generations were retained. The retention audit used
immutable upload evidence and archive manifests for large parts, and pinned or
direct reads for other objects. The DVC scientific backups were verified on
the remote. This count reports simulation completion for generic trees with
species-inspired geometry, a 0.5 m grid and imposed ignition. It does not
establish ignition rates for real species.

On November 6 the user authorized continued simulation under a cumulative
spending ceiling reconciled against the billing export. The fourth continuation
starts at index 586, the first of 945 untouched cases. The 1,022 verified
results and all previously interrupted, deferred or failed identities remain
excluded from new submissions. The independent admission guards allow up to
18 singleton jobs. Each job retains its original deck, checkpoint policy and
scientific acceptance checks. New admissions end with sufficient time for
cleanup before the original temporary permissions expire.

The first November 6 controller stopped before launching an epoch when its
service-account request received HTTP 403. Its execution record is retained.
The replacement uses a unique parent claim. Before submission, the workflow
service account successfully started no-solver case, epoch and parent executions,
and the failed parent was verified to have submitted no simulation. The
replacement continues from the same untouched index 586.

The November controller stopped admitting new jobs after Batch reported that a
VM was recreated during case 824 (exit 50006). Its failed-task record and two
checkpoint manifests remain in private storage. The case is excluded from
scientific acceptance. A separate scheduler revision recognizes this exact
infrastructure event, records the interruption, and continues other untouched
indices after cleanup. Spot preemptions retain separate counts. The bounded
drain watcher checks terminal state, complete claims, empty resources,
scientific outcomes and the current spending estimate before a single new
submission. Inspect its receipt before reporting a restart.
