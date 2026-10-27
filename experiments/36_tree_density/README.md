# Experiment 36: denser in-range tree ignition data

User authorized launch and private input upload to `gs://tmrw-wildfire-20261015-trial/density36/`. Google approved capacity for 24 four-core C3 workers. Public publication is not authorized by this launch.

Exactly 1,560 new simulations: four diagonal ignition angles (45/135/225/315 degrees) at existing 1/3/5 m/s winds (720), plus 2/4 m/s at seven angles (0/45/90/135/180/225/315; 840). Existing 520 histories are retained, making 2,080 histories and 2,040 unique configurations. No new replicas, South 270-degree cases, or missing 108 old-grid cells are silently added.

Same simplified physics: generic 3 m diameter vegetation cones, crown heights 4/6/8/10 m above a 2 m base, 1,600 frozen weighted particles in four material classes, loading 0.7/1/1.3, uniform water-to-dry-mass moisture 0.06/0.12/0.18/0.24/0.30. Steady wind along +x. A 60-degree ignition arc at radius 1.2 m and height 2.1 m imposes 1500 C for 20 s. Domain 24x16x16 m, 0.5 m cells, 180 s simulated time, 2 s particle snapshots. No trunks, buildings, or embers; this is not physical validation or a stronger-wind study. The existing 48 legacy geometries remain documented in the old dataset.

## Execution and evidence

`prepare.py` creates and hashes all decks, checks exact reconstruction of an old deck and excludes duplicate configurations. No local FDS or model training. `cloud.py prepare` creates 131 bounded job groups and compressed private input packages. The worker verifies the package SHA256 and each deck SHA256. Eight offline upload-failure tests check immutable creates, uncertain outcomes, matching content, and bounded retries. Each cloud case must pass an actual Linux checkpoint/resume test before its solve.

One dispatcher owns all submissions and collection. It runs six coverage simulations first and compares their initial material density with the frozen reference, full horizon and restart hashes; only a passed coverage audit releases the remaining 1,554 cases. Maximum 24 jobs concurrently. No automatic paid retries; any interruption/failure preserves available evidence and stops further dispatch. Previously completed cases are immutable. Each case writes 30-s physical-time restart checkpoints; a failed run must be diagnosed and separately resumed, never blindly resubmitted.

Per group: 4 h 26 min task maximum, 4 h 57 min absolute workflow deadline, 20 min queue limit, zero Batch retries. A case has a 20 min solve limit with a bounded stop grace. Raw archives and summary hashes are retained in the private bucket; coverage raw files are also downloaded and SHA256 checked. Other raw files remain in GCS until downstream extraction/archive. Completion must verify all 1,560 hashes and output inventories, cleanup and exact permission removal. A workflow cleanup success alone is not scientific success.

## Budget and expected duration

Before launch: posted charges $28.6652 plus $0.56195 measured compute wholly after billing coverage = $29.22714 project estimate, not an invoice. $125 cumulative cap. Reserve $52.40 for 131 CPU jobs (each $0.40 maximum at conservative $0.08/hour), $10 storage/overhead and $8 later unchanged-model evaluation: $70.40 maximum allowance, leaving about $25.37 unallocated. Allowances are not spend. Reconcile measured VM lifetimes, then replace estimates with matching billed rows; never add overlapping billing and runtime totals.

Previous 472 cases averaged 352 s per solve. With 24 workers allow roughly 8–12 hours including validation, scheduling and I/O; capacity is not guaranteed. Expected new raw storage is approximately 147 GB, with ongoing storage charges until a separately authorized archival/retention decision. The $10 overhead allowance is finite, not indefinite free storage.

## Evaluation after collection

Merge with old cases and rebuild grouped ten-fold splits, retaining replicas together. First compare using the unchanged plain four-state GRU and frozen Scorecard V1: water kg, derived dry fuel kg, vegetation fuel-gas release kg/s, and surface-heating index K (not stored energy). Char is inert ash and derived fuel uses yield 0.75. No gates, monotonicity clamps or positivity constraints. Report active/quiet/weak/transition errors, 16-s headline, all four features, simulation denominators, no-change baseline, invalid states and scenario distributions. Reshuffled previously examined data is not pristine. More data also changes updates per epoch; report updates and stopping conditions.

Conclusion pending: these are input/launch checks, not evidence of improved accuracy. Hyperparameter exploration is planned separately; none is launched here.

## Startup interruption — 26 October UTC

The first coverage job failed before any solver ran: the registry seven-day deletion policy had removed the pinned image. No bulk jobs started. VM/job/disk cleanup and exact read-grant removal verified. Measured compute estimate $0.00113; project estimate $29.22828. The original Linux solver is preserved locally and its SHA256 exactly matches experiment32. A replacement runtime recipe is prepared without recompiling the solver, but no build/relaunch has occurred. Approval is required under the no-automatic-paid-retry rule. Keep the original execution and packages unchanged; corrected coverage needs a new prefix and image-existence check. Runtime libraries may differ and require Linux resume and full coverage validation.

## Approved restoration

User approved a $1 bounded repair and continuation. Cloud build58f55a79-1946-4a50-9c10-a22807acd734 succeeded with the unchanged solver binary and checked dynamic libraries. The replacement image is pinned to sha256:b4bc461b8ebf2b4b3d0b7376ad69dcf19055f8abb5f1001ebd952f1d84f3cfb7. `active-groups.json` selects replacement coverage `x36-coverage-r1` plus the 130 originally unsubmitted bulk groups. Original inputs and workflows remain preserved. The offline repair audit proves all scientific inputs and worker code unchanged; only image and replacement coverage identity differ. Every launch now checks registry image availability first. Actual full solver/resume checks remain mandatory on cloud.

## Effective concurrency

Six coverage cases passed. Twenty bulk groups were submitted before Google rejected the 21st temporary prefix-read grant: a principal/role can have at most20different conditional bindings. Dispatcher concurrency is therefore20, while compute quota remains24. Existing jobs are unchanged and no paid job is retried. Keep the per-job narrow grants rather than widening access. Expected total duration is closer to10–14hours, subject to capacity.

## Global quota queue interruption

Groups009–020 reached the20-minute queue deadline with zero recorded run duration. The regional96-core quota had been approved, but the global32-core limit prevented allocation. Global96 was approved too late for these waiting groups. All12cleanup inventories are empty and temporary grants removed. Groups001–008 continue under collection-only monitoring; no new submissions occur while replacement approval is pending. A prepared, inactive replacement plan covers144cases using byte-identical packages except group identities. Maximum new allowance4.80USD within125cap. New launches now check globalCPU plus regionalCPU/address/disk limits. Do not resubmit original job IDs.

## Approved overnight continuation

The user approved the twelve queue replacements ($4.80 maximum) and subsequently authorized necessary diagnosed restarts and repairs overnight within the $125 cumulative cap. The original failed IDs remain preserved; new IDs009-r1 through020-r1 use byte-equivalent scientific packages. Global and regional quotas are checked before each launch. The collection-only monitor was stopped and a single dispatcher resumed with the activated manifest. Existing completed/running executions are retained. Additional recovery must diagnose the cause, preserve partial outputs/checkpoints, reserve its full allowance and avoid duplicate submissions; this authorization does not expand the scientific campaign or authorize public publication.

## Sleep-independent cloud orchestration

The local dispatcher has been replaced by `fds-density36-parent` in Google Cloud Workflows. Its immutable queue contains only groups029–130 (102 groups,1218cases); previously submitted groups are excluded. Twenty parallel branches use the byte-identical Batch job definitions and existing watchdog permissions, retain the same queue/task deadlines and cleanup, and verify full-horizon/resume/deck/binary summaries. An immutable parent lease and per-group intent prevent accidental re-execution; paid job creation has no automatic retries. Transient read requests use bounded retries. Inputs/results remain in the private GCS bucket; local downloads, full raw SHA verification, DVC mirroring and analysis can resume when the laptop is awake. Workflow completion is not a claim that this local archival work is done. A $1 orchestration allowance is reserved within the cumulative cap. Worker/controller read permission is limited to the campaign prefix and expires after48hours.

Cloud parent first execution: `4b1e487c-a806-408c-828b-7d012a8a31ff`, started2026-10-26T16:13:40Z. First wave observed in Batch with local dispatcher stopped. Cloud ownership is recorded in `orchestration/cloud-owner.json`; local submission tools refuse to run while this marker exists. The initially attempted child-workflow invocation design is retained as diagnostic provenance; the deployed revision uses `parent-inline.yaml` and requires no new workflow-invocation permission.

## Audited dataset completion — 27 October 2026 UTC

The exact case-level audit now passes for all1,560 new histories, including29 unfinished cases recovered after four Spot preemptions. It verifies148,500,758,857 raw archive bytes by SHA256, checkpoint hashes, frozen decks and extracted91-frame four-state histories. Full raw/checkpoint archives remain in private GCS; compact material inputs and extracted/merged datasets are mirrored through DVC. The merged dataset has2,080 histories and2,040 unique configurations; old520 states and timestamps are bitwise preserved. See `results/dataset-completeness.json` and `results/learning-data.json`.

An earlier completion estimate was wrong: a live-job-only check missed terminal preemptions088/093/115. The final exact-case audit, rather than workflow success or an empty job list, establishes coverage. The original parent also failed on summary decoding; its successful jobs were independently verified and its final orphaned cleanup repaired without repeating simulations.

Project job, VM and disk inventories are now empty, and both exact temporary campaign-prefix read grants have been removed. Full raw/checkpoint objects were not deleted. Evidence is in `results/cloud-campaign-closed.json`.

Model fitting and accuracy evaluation have not started. CPU checks verify grouped partition isolation, train-only normalization invariance and synthetic model behavior; they are not accuracy evidence. The ten-rotation runner retains the byte-identical5,796-parameter plain GRU and training equations. The larger dataset changes optimizer updates per epoch; the old runtime deadline cannot be assumed sufficient. Cloud runtime/budget checks and all-selection-before-test protection remain required within the reserved model allowance. The simplified geometry, imposed ignition, derived state definitions and lack of physical validation described above still apply.

## Completed non-overlapping model baseline and authorized report publication

The ten-rotation run completed successfully. Collection verified all 5,860 manifest objects (1,635,548,567 bytes), every epoch checkpoint, and all ten selections before any test output. Cloud jobs/VM/disks were empty and the exact temporary training read grant was removed. Full checkpoints and forecasts remain privately preserved and DVC mirrored.

At nominal 16 seconds during active periods, pooled error relative to mean absolute simulation magnitude is 7.11% water, 6.42% dry fuel, 30.81% fuel-gas release and 13.53% surface heating. The model improves on no-change MAE by 82.36%, 83.67%, 82.18% and 88.93%, respectively. During quiet periods it loses to no change on all four outputs. Exact physical MAEs, denominators, all horizons, scenario distributions and invalid predictions are in the report and results JSON.

Material training detail: the current baseline uses non-overlapping curriculum windows, including a shorter final window. At 16 steps it uses five full windows and one ten-step tail per history. Evaluation uses all valid origins. This distinction was not adequately disclosed earlier. The user explicitly requested a separate rerun retaining the 1/8/16/32-step curriculum but using stride-one full windows at every stage (90/83/75/59 windows per history).

The user authorized public publication of the report and derived metrics, not new raw simulations. Published report: https://wdavies-fire-reports.static.hf.space/density36-baseline/index.html . Publication hashes and commit are in results/report-publication.json. Comparison with the earlier 520-history run changes held-out populations, fold assignment and optimizer work, and does not isolate a data-only causal effect. The overlapping rerun must start only after baseline publication and Git/DVC preservation are verified; it has not yet launched.

## Authorized matched stride-one pair — 27 October UTC

The user now requests both the original plain four-state GRU (5,796 parameters) and the original soft-gated four-state GRU (5,895 parameters), sequentially on one cloud L4. Rotation0 is chosen by the frozen ordering, not by scores: 1,662 training histories / 1,632 configurations, 210 validation histories / 204 configurations, and 208 test histories / 204 configurations. Both validation selections must be frozen before either test evaluation. These are two single-split results, not ten-fold aggregates.

Both retain the 1/8/16/32-step curriculum, batch size256, AdamW recipe, seed3516, and100–400epoch/patience policy. Full stride-one windows yield90/83/75/59windows per history; the old non-overlapping tail windows are absent. Existing transition weights remain, so interior transitions receive repeated exposure and optimizer updates increase. This changes training work as well as coverage.

The model implementations are preserved byte-for-byte in separate modules. The gated arm retains its original0.1 auxiliary binary-cross-entropy loss and three trailing-window activity labels. Labels and rates replay bitwise on all520old histories. Weak-rate labels are excluded from gate supervision. Water/fuel increment gates and gas suppression are soft, heating is ungated, and there are no hard physical constraints. Initial gated gas is multiplied by sigmoid(4), approximately0.982; the plain model starts at exact persistence. These distinctions are part of the requested architecture comparison.

Offline checks pass both models'32-step gradients, serialization, reporting, prefix isolation and train-only normalization. The bounded cloud timing execution is `ef09117c-5248-4aa1-aa63-869d5aaa3c8a`, supervised by `fds-gpu36-paircheck01` with no automatic retries. Full training awaits measured runtime budgeting. The training workflow will supervise the GPU independently of this laptop; each epoch preserves model, optimizer, RNG, history and selection state privately. A synthetic nonempty-optimizer continuation check runs in cloud before fitting. A deadline checkpoint requires diagnosed and separately budgeted continuation, never a blind rerun.

After completion, add both single-split results to the existing Simple Scorecard and create a new gallery containing only their shared208test histories. Preserve earlier reports and galleries. If both runs finish before08:00Pacific on27October, prepare the same pair on the next frozen rotation1, subject to the cumulative125USDcap; do not choose folds from test performance.

The pair preflight succeeded and its exact read grant was removed after empty job/VM/disk cleanup. Full measured epoch times (1/8/16/32steps) were2.90/11.27/19.17/29.12seconds for plain and4.05/20.02/34.98/54.19seconds for gated. The two-arm100–400epoch measured component is1.46–8.46hours, excluding optimizer/upload/forecast overhead; conservative totals with2xcompute,2s/epochuploads and30minforecasts are3.53–17.87hours. These are bounds/projections, not completion promises.

Training was submitted once as workflow `fds-gpu36-pairtrain01`, execution `c74635a4-40f1-4b9c-9cd6-c3c0d9097e05`, private prefix `density36/model-pair-training01/`. Soft training deadline18hours, task18.25hours, VM age18.5hours, absolute workflow19hours, allocation queue20minutes, zero automatic retries. Maximum reserved allowance15.20USD. Project estimate plus outstanding reservations including this run is96.7302USD against125USD. No new FDS simulations were launched. Both models run sequentially on one GPU with a cloud workflow supervisor.
