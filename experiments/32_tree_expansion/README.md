# Tenfold tree dataset expansion — authorized, cloud setup

Aim: increase distinct training configurations40→400, compare geometry-aware snapshot CNN and snapshot-plus-recurrent-correction on40fresh physical configurations, and quantify sensitivity to FDS random seed. Current models fail a known weak-burning training example; data growth is a testable intervention, not a guaranteed cure. Training-fit checks remain mandatory and seed replicas are not counted as independent physical configurations.

## Variations

- Generic cone crown heights4/6/8/10m, above a2m base; diameter3m fixed.
- Moisture0.06/0.12/0.18/0.24/0.30kg water/kg dry vegetation, applied uniformly to all four vegetation material classes. These are experimental levels, not species validation.
- Dry-fuel loading multipliers0.7/1.0/1.3. Height scales total dry fuel proportionally to preserve density before loading changes; moisture adds water without increasing dry fuel.
- Wind1/3/5m/s along+X. Ignition at0°downwind,90°crosswind,180°upwind; fixed60°source arc.
- 540possible discrete combinations;432selected new configurations. Integer-constrained sampling balances every factor marginal to within one configuration within each new split. It does not exhaust all higher-order combinations.
- 20selected configurations (12train/4validation/4test) have three distinct seeds each; the remaining412have one. This adds40runs, not60, because the first seed is already included. Every seed is recorded and all472new seeds are distinct. Replicas share identical decks except case name and seed, including exactly the same frozen vegetation particles.

## Splits and reuse

| Split | Unique configurations | Total trajectories including seed repeats | New FDS runs |
|---|---:|---:|---:|
| Train |400|424|384|
| Validation |40|48|40|
| Fresh test |40|48|48|
| Total |480|520|472|

Reuse40existing training and8existing validation runs. Previously examined test cases remain excluded. Legacy data are not uniformly distributed across the new factor grid: they mostly have the original moisture and tree geometry. Report legacy regression checks separately from the32new validation configurations; do not conceal this distinction in a single selection score. All new splits come from the same balanced discrete factor space. Hold out complete physical configurations, including every seed replica.

## Fixed simulation choices and limits

Uniform0.5m mesh in24×16×16m,180s horizon,2s field outputs. One fixed3m-diameter cone family;1600frozen vegetation particles, deterministically scaled in height and weights. Four generic material classes. Artificial1500°C stationary ignition particles operate for20s (ramp off by20.1s). No trunks, resolved branches, buildings or embers. Ground remains nonflammable and heatable. The shortest crown tops at6m, tallest at12m; top-boundary clearance varies and this campaign is not a new domain/grid convergence study. Fixed-seed numerical repeatability across hardware/thread changes is not assumed.

The initial-data checks verify coordinates, weights, moisture-dependent total mass and invariant dry fuel for four0.1s native solves, including a seed pair. They do not establish fire accuracy or the magnitude of seed variability. A same-Linux checkpoint-resume check remains required before full cloud solves. Preserve periodic restart files and raw particle/slice/boundary evidence.

## Learning and evaluation contract

Both models must receive moisture explicitly before training; the current fixed0.12 assumptions must not survive in input encoding or material initialization. Use consistent dry/wet material semantics verified against raw FDS. Snapshot uses geometry summaries plus physical conditions; recurrent correction additionally uses the density grid and predicted state. Seed is not a physical model input. A deterministic prediction cannot identify an unobserved random realization: report ensemble means and run-to-run spread for the repeat subset alongside per-run errors. Sample configurations uniformly, then a seed within configuration, to avoid tripling the training weight of repeated configurations. Fit both models on the same splits and report complete training histories, especially weak-burning examples. Freeze weights, predictions and baseline before viewing any new test outputs. No future FDS state at inference. Compare temperature-rise percentages, heat-release histories, radiation, airflow and fire-region overlap; source-on and source-off intervals separately. Keep existing scientifically relevant metrics rather than replacing failed measures with easier ones.

## Cost and execution proposal

User approved the $25 campaign cap. The coverage batch is submitted. Previous12completed runs averaged347s solver wall time (range274–412s) on4vCPU. Proposed6concurrent4vCPU Spot workers,40groups of up to12cases, then bounded Spot GPU fitting/evaluation. Allow1200s per solve,4.5h maximum VM lifetime per group and5h absolute controller deadline including queue/cleanup. FullCPUreservation$16, GPU$3, storage/ancillary$4, margin$2 = proposed$25cap. Expected total$5–$9; ETA10–14h conditional on Spot availability and similar runtimes. These are conservative planning-rate estimates, not current SKU quotes or invoice spend.

Keep bulk raw evidence/decoded fields in the same cloud region and download selected visualizations, rather than moving the entire dataset to the laptop. Expect roughly40–60GBcompressed raw data plus50GBdecoded fields; retention beyond this campaign incurs ongoing storage charges. Reserve every paid group's complete allowance before submission. No automatic paid retries or recycled reservations. Cloud-side deadlines and cleanup required. GPU training will need streamed/per-case data access and adequate disk, not whole-dataset RAM loading. Expanded cloud dispatch, preprocessing and moisture-aware training integration remain to be wired before launch under an approved budget.


## Execution handoff — 2026-10-20

User approved $25 total and requested training. Central ledger is budget.json. Four dollars ancillary is reserved. First coverage attempt reserved $0.40 and failed only an added checkpoint checker: FDS took one timestep to0.1s, then resumed step2 to0.15s; check incorrectly required a row strictly between0 and0.1. Retained Linux failure archive/checkpoint is data/failures/coverage00.tar.gz; cleanup confirmed empty. Reservation remains. Corrected check verifies timestep/time advance and successful restart. Corrected group x32-coverage-00-r1 separately reserves$0.40. Its scientific decks are unchanged. Original jobs directory is retained, groups.json lists the corrected coverage.

A single locked dispatch_development.py session collects small summaries and object metadata, downloads ONLY six coverage raw archives for exact initial density/checkpoint verification, then launches development groups up to six at a time. Check process and errors before restarting; never duplicate jobs or collectors. No automatic paid retries. Current persistent tool session70816; initial nohup attempt did not survive and no duplicate was found. Cloud cleanup works independently of this laptop. Dispatcher requires the laptop/controller host awake to submit later groups; existing workers finish and clean up if it sleeps. Follow-up automation is enabled every15minutes for diagnosis and onward training.

Prepared model changes:13snapshot inputs (moisture appended), hybrid moisture replaces hardcoded0.12, configuration-uniform then seed-uniform sampling,32000snapshot updates and1600full hybrid trajectories. Snapshot warms from prior geometry model with zero-initialized moisture column; hybrid from prior sequence weights with reset field correction. Both use the same data. Selection uses new-distribution validation balanced by configuration; legacy regression reported separately. validate_learning.py passed CPU inference-only shapes and raw record-reader checks; no local model training.

prepare_inputs.py created472development records and48fresh-test input descriptors. prepare_gpu.py creates1.08GB overlay and cloud preprocessing/training workflow (200GBdisk,8400s task,9000sVMage,10800sabsolute;GPUtraining reservation$2.50, leaving$0.50of plannedGPUallowance for evaluation). Cloud preprocessing downloads one development raw archive at a time, verifies SHA/deck/checkpoints and initial moisture-adjusted geometry, extracts six fields and material states, then removes only its temporary VM copy. Raw GCS objects remain. Input descriptors for fresh tests use frozen geometry and dry-mass reference, never fresh FDS output. Predictions upload as separate objects; weights/small reports archive separately to avoid multi-GB RAM bundles.

Next: inspect coverage/dispatcher; repair genuine issues independently within cap. Re-run prepare_gpu.py after any training/source change BEFORE uploading/launch. launch_learning.py gates all development completion, uploads immutable overlay, adds24h scoped input-read condition, reserves$2.50 centrally, verifies deployed workflow then submits. This path is prepared but not yet exercised. collect_learning.py fetches small results/weights and checks cleanup. Test launch checks frozen local source/weights and remote prediction MD5 against freeze; full SHA verified during evaluation. Fresh-test dispatcher and cloud evaluation/visualization still need implementation before test stage. Do not report models trained until cloud completion evidence exists. Remove temporary input-read condition after evaluation. DVC stages must adopt collected evidence without rerunning paid work.

CPU planning bound actually enforced by current controller is5h absolute including queue, with15960s task limit; startup/cleanup fall within the absolute deadline, not a separate4.5h VM-age monitor. $0.40 covers5h at planning rate$0.08/hour; ancillary reserve covers disks/storage. Six cases in coverage, remaining418development split into35groups,48fresh tests4groups. PlannedCPU16 plusfailed.40, GPU3, ancillary4 leaves1.60unallocated within25. Reservations are not billed spend.

First corrected full solve x32_000_s0 completed180s in235.7s on4CPUcores; raw archive and summary uploaded. This is one case, not an updated campaign timing estimate. GPU launch and collection scripts are now prepared; final fresh-test evaluation/visualization remains to be wired during development generation.


## Follow-up integration — 2026-10-20 evening

Four of six corrected coverage solves have uploaded full180s results (wall times236,331,337,161s); remaining cases still active at this checkpoint. Existing development dispatcher PID73331/session70816 remains the only CPU controller. A separate locked stage coordinator continue_campaign.py (PID74482/session83598) now waits for development completion, then invokes guarded launch_learning.py, collect_learning.py, dispatch_tests.py, prepare_evaluation.py, launch_evaluation.py, collect_evaluation.py and visualization. It does not duplicate the development dispatcher. Both stop on errors without paid retries; inspect results/*error.json. Do not launch another coordinator or manually duplicate its transitions. Actual cloud GPU/evaluation execution still untested; syntax and small input/metric checks passed.

Held-out evaluation plan is evaluation-plan.json and is included in the training package and prediction freeze. Existing absolute metrics retained; added percentages use FDS temperature rise above20C, reference heat/radiation and reference velocity magnitude. Truth-hot and union-hot masks are reported separately; undefined denominators give null. Identity and doubled-rise tests returned0% and100%. Evaluation averages seeds within each configuration before averaging40configs; the four three-seed test groups also compare deterministic predictions against mean FDS fields and report run-to-run heat/peak spread. The first test configuration at each height is selected for animation BEFORE reading outcomes. Rendering uses maximum-through-y projections of gas temperature/heat-release density with shared clipped scales, not physical flame geometry.

The six predicted fields remain gas temperature, volumetric heat-release rate, three gas velocity components and integrated radiation intensity. They do not include solid-surface ground temperatures or embers. The hybrid's internal material state is pooled to2m, while predicted gas fields retain0.5m output cells. This expansion retains the prior model architecture and test scope rather than claiming a full FDS replacement.

Training package regenerated after adding frozen evaluation plan and percentage metrics; GPU launch now checks every current source/input against learning-input-freeze before submission. Cloud evaluation receives only frozen models/predictions and new test outputs, never fits. Training predictions remain GCS objects verified by MD5 before test launch and SHA256 in evaluation. Small projections/reports return locally; raw archives stay immutable in GCS. Scoped24h input-read grant is removed by final collector. Final narrative report and DVC adoption of newly generated outputs remain required after coordinator completion.

Full split audit now checks physical parameters across both48reused and472new trajectories, not just IDs:480unique physical configurations,400/40/40train/validation/test, zero cross-split overlap. See results/full-split-audit.json.


## Coverage accepted and development started

All six corrected coverage solves completed180s and passed frozen initial density/moisture and checkpoint checks. The cloud inventory confirmed exactly six RUNNING development jobs/VMs, with coverage resources cleaned up. Reservations are$7.20 including$4ancillary and the retained failed$0.40 attempt, not invoice spend. Coverage runtime range161–412s per4-core solve.

validate_cloud_data.py exercises the exact cloud preprocessing implementation on retained coverage archives without training or paid work. It caught a NumPy compatibility issue: newer local NumPy removed trapz, whereas the cloud image may predate trapezoid. fields.py now chooses the available equivalent. After correction all six complete field/material histories decoded successfully, including exact180s endpoints and frozen moisture-adjusted geometry. GPU launch requires this check; training package regenerated before submission.

Post-source (t>=21s) integrated fuel-release mass was13.5428kg vs14.3071kg for the same configuration with two seeds,5.49% difference relative to their mean. Corresponding peak gas temperatures1474.5C and1430.3C. Other coverage cases include weak burning (x32_343_s0:0.0317kg,159.5C) and stronger outcomes. These are initial coverage observations, not an ensemble estimate or physical validation; see results/cloud-data-check.json for direct raw-field/device-derived values. Seeds leave the frozen tree unchanged.
