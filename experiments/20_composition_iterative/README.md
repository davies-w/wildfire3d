# Experiment 20: bounded composition study

Aim: obtain distinct igniting and non-igniting vegetation arrangements, then test whether shared graph interactions predict unseen three-crown scenes better than an independent-crown model and aggregate baseline. This is a synthetic FDS surrogate test, not validated real-property risk.

## Budget and execution

The user authorized $2 incremental cloud spend. `budget.json` reserves each batch's complete conservative allowance before submission. Reservations are never automatically recycled. One Spot c3-standard-4 worker, no retries or image builds, with cloud-side deadline and cleanup. The first five diagnostic cases reserve $0.15, leaving $1.85 unreserved. The rate used is $0.065744/hour plus $0.07 ancillary allowance for this batch. These are estimates, not a hard billing cap.

`control.py prepare <spec.json>`, `launch <name>`, `status <name>`, and `fetch <name>` manage explicit bounded batches. Launch requires passing local startup checks and no existing jobs or VMs.

## Initial diagnostics

Two burner-only controls reproduce source positions in previously igniting diagonal and non-igniting aligned arrangements. A third retains only the near-house crown but both source positions. Two new random seeds repeat the near-threshold aligned arrangement. These distinguish direct burner contribution, vegetation interference, and stochastic sensitivity. All retain the original 350 C house ignition rule, 0.5 m cells, particle vegetation, 90 second horizon, and default 30 second source exposure.

Additional outputs include convective/radiative/total wall heat flux, velocity and temperature slices, and per-crown particle mass. Local 1.05 second startup checks passed for absent vegetation, removed crowns, and a new geometry. They do not establish physical accuracy.

## Learning protocol

Training and validation use only one/two-crown scenes, with entire validation geometries held out. Both splits must contain both classes overall; permanently negative layouts are legitimate controls. Require at least three distinct positive training geometries before fitting. Source duration remains 30 seconds for this first model; shorter-duration diagnostics are excluded unless features and protocol are revised before training. All three-crown confirmation predictions must be frozen before inspecting their simulation outputs. If test coverage is insufficient, report that limitation; any subsequent model tuning requires a fresh test set.

Graph, independent-crown, and aggregate predictors share the same development evidence and five training seeds. Epoch selection uses class-balanced validation Brier score. Report class-specific recall, Brier score, individual cases, uncertainty across training seeds, and comparison with trivial baselines. A tiny test cannot establish field accuracy or generalization to other houses, vegetation, moisture, or winds.

Status: first diagnostic batch launched; no new model results yet. Existing experiment 18/19 evidence will be reused with original provenance, without counting old three-crown test labels as new held-out evidence.

## First completed control

`control_AC_bare` reached house ignition at 24.558411 s without vegetation; the device peak wall temperature was 402.52575 C. Raw `fds2ascii` west-wall BURNING RATE, averaged over 0–90 s, had a positive maximum patch mean of 0.0041895 kg/m²/s at (14,12,0), confirming wall burning. The corresponding earlier vegetated case ignited at 13.033506 s. Thus vegetation is not necessary for this positive label; do not treat the old dataset as proof of vegetation-mediated ignition.

`geometry01.json` is superseded pending matched exposure controls. `exposure01.json` proposes six bare/vegetated controls at 10/20 second source duration with a $0.20 reservation, not yet launched. If the learning protocol changes duration, update features or use a consistent new duration; current model features assume 30 seconds.

Continuation is configured through the app follow-up `continue-wildfire-composition-experiment`, every ten minutes while work remains. `results/continuation.json` records the current handoff; cloud budget remains global across these follow-ups.

The second burner-only control, `control_AD_bare`, did not ignite. All six house boundary orientations were checked with fds2ascii over 0–90 s: its maximum time-averaged BURNING RATE is zero, while the first bare control has positive burning. The initial control difference therefore persists without vegetation; geometry-dependent burner heating is a demonstrated confound. The remaining three diagnostic cases are still running; no second batch has launched.

## Four-case interim result

Keeping the aligned burner positions fixed but adding only the near-house crown (`control_AD_without_D`) produces ignition, whereas the bare aligned control does not. All-house raw boundary burning confirms the difference, so vegetation does affect ignition in a matched comparison. The full two-crown aligned scene at random seed 4321 also ignites, whereas the original seed 1234 did not. This is seed-sensitive near-threshold behavior; do not choose favorable seeds to manufacture positive coverage. Retain seed repeats and report uncertainty. The fifth case (seed 5678) is still running.

## Diagnostic batch complete

All five cases completed and raw boundary/device ignition labels agree. The final full-vegetation repeat (seed 5678) did not ignite: together with the original seed 1234 and positive seed 4321, the aligned two-crown scene has one ignition in three runs. This sample is too small for a reliable probability estimate. Cloud workflow succeeded after 1942.8 s and cleanup confirmed zero VMs, disks, or Batch jobs. Compute upper estimate is about $0.0355, plus the reserved $0.07 ancillary allowance; this is not invoice-verified billing. The full $0.15 reservation remains charged to the experiment ledger.

The next batch is `exposure01`: six matched bare/vegetated cases at 1700 kW total source power, comparing 10 and 20 second source durations. Conservative maximum estimate is $0.1822 (75 minutes at $0.065744/hour plus $0.10 ancillary allowance), with a $0.20 reservation. It keeps the same 90 second horizon, particle fuel, and house ignition rule. Use results to select exposure duration before expanding learning data.

## First shorter-exposure control

The diagonal burner-only scene with 10 second source exposure (`exposure_AC_10_bare`) did not ignite the house during 90 s: fds2ascii readings across all six house boundary orientations have zero maximum time-averaged burning rate. The corresponding 30 second burner-only exposure ignited at 24.558411 s. The matched 10 second vegetated case is still running; no claim of vegetation-mediated ignition under this shorter protocol yet.

## Shorter-exposure interim comparison

For the diagonal arrangement, both 10 second cases (bare and vegetated) remained non-igniting through 90 s. The 20 second bare case also remained non-igniting. All three labels agree with all-house fds2ascii boundary burning-rate checks. Ten seconds therefore removes the known positive in this matched pair; do not expand a 10 second training protocol on the assumption that it preserves ignition. Await the 20 second vegetated result before choosing the development protocol.

## Twenty-second matched positive and development plan

`exposure_AC_20_vegetation` ignited at 13.022085 s; its matched bare control did not ignite within 90 s. Across all six house boundary orientations, maximum 0–90 s mean burning rate is 0.0097608 kg/m²/s with vegetation and zero without it. This establishes vegetation-dependent ignition for this particular scene/exposure, not for all source powers or geometries.

The prepared, unlaunched `development20` batch has 20 cases: four training geometries (A, AB, AE, AG) at 300/1700/3200 kW with 20 second exposure; held-out validation geometries AC/AF at those powers, reusing the existing AC1700 case; and three seeds for near-threshold AD1700 at 20 seconds. The $0.32 reservation covers a three-hour deadline estimate of $0.197232 compute plus $0.10 ancillary allowance. It cannot launch until the current exposure batch completes and cleanup is verified.

The model protocol now includes source duration explicitly: 12 node features in graph/independent-crown models and 10 aggregate baseline features. Prior 30 second cases can be reused, while confirmation uses 20 seconds. Training requires at least 12 twenty-second training cases and at least three positive geometries at that duration. Differentiability, permutation invariance, and synthetic train/freeze/predict/evaluate checks passed. No real models have been fit yet.

## Development acquisition launched

All six exposure cases completed and cloud cleanup was verified. The final AB10 vegetated case ignited at 13.037046 s; its bare control did not ignite. Both labels passed all-house raw boundary checks. We therefore retain useful 10/20/30 second development evidence with duration explicitly represented.

The twenty-case `development20` batch launched, with a $0.32 reservation and cloud-side three-hour deadline. Total reserved allowance is $0.67 of $2; $1.33 remains unreserved. One-shot local completion collects evidence, checks cleanup, and runs raw boundary diagnostics. The assembled learning dataset excludes bare and partial-vegetation controls because the current predictor assumes a source beneath each crown. Existing and new full-vegetation seed repeats are retained. `dvc repro development` will assemble and verify the completed dataset; training follows only after class and geometry coverage checks.

## Prespecified confirmation plan

While development runs, `confirmation-plan.json` fixes four unseen three-crown compositions (ABG, ACG, AEG, ADG), source powers 300/1700/3200 kW, 20 second exposure, and two seeds (4321,5678): 24 test cases. Every outcome will be retained, including seed disagreements. All anchor locations are represented in development data. The batch is not prepared or launched; weights and predictions must be frozen first. A $0.40 reservation would cover four hours of compute plus $0.10 ancillary allowance (maximum estimate $0.3630), within the remaining $1.33 allowance. Low/high powers improve the chance of both classes but do not guarantee coverage.

## Models trained and confirmation launched

All 69 development examples passed raw-boundary ignition checks. Four model types were fit with five optimization seeds each: graph (1182 parameters), independent-crown (1182), aggregate auxiliary-output (682), and ignition-only logistic baseline (10). The latter uses the same aggregate inputs and learns ignition only. All use the same training/validation splits and validation epoch-selection criterion. Synthetic checks passed before fitting.

Weights and all 24 held-out scenario predictions are frozen in results/frozen-weights.json and results/frozen-predictions.json. The confirmation20 cloud batch is launched with a $0.40 reservation, total $1.07 of the $2 allowance. Its conservative deadline-based estimate is $0.3630 including ancillary allowance. No test output informed model selection. finish_confirmation.py automatically verifies cleanup, preserves raw evidence, checks labels and runs final evaluation. No further model fitting is permitted against these test outcomes.

## Completed result

All 24 held-out simulations completed and all raw-boundary ignition checks passed: 13 igniting and 11 non-igniting runs. The five-fit graph ensemble classified 19/24 correctly (Brier 0.179), compared with 13/24 for independent-crown (0.246), aggregate (0.214), and ten-parameter ignition-only (0.215) ensembles. Graph detected all13 ignitions but produced five false positives. Individual graph fits vary substantially (54–88% accuracy); this tiny, fixed-house study supports only a preliminary result. See [full findings](results/findings.md) for limitations, seed disagreements, and provenance.

The experiment is complete and its recurring follow-up is paused. No cloud VMs, disks or Batch jobs remain. Conservative total estimate is $0.725 including ancillary allowances, versus $1.07 reserved and $2 authorized; actual billing is not verified. No more runs are scheduled.


### Ignition and graph GIFs

`results/visualizations/fds_ignition.gif` renders archived wall-temperature boundary data and vegetation particles using Smokeview for `confirm20_ACG_3200_s4321`. Recorded house ignition is 9.5052105 s (see `data/test.json`); the archive does not contain volumetric flame/smoke output. Colours display wall temperature, not flames. No new simulation or cloud spend is required.

`results/visualizations/graph_messages.gif` shows encoding and two message-passing rounds from the frozen graph checkpoint with training seed 11 (first predefined seed), for that same scene. Node colours show hidden-state magnitude; arrows show the 12 largest of 56 directed messages. These are computational stages, not physical time, temperature, or causal importance. The feature heatmap and `data/visualization/graph_trace.json` preserve actual values. This checkpoint predicts 86.0%; the five-checkpoint average is 93.2%. These are toy-model outputs, not calibrated real-property risk estimates.

Reproduce locally with `dvc repro visualize` (requires Smokeview graphical rendering on macOS). Scripts: `visualize_event.py`, `visualize_graph.py`.


### Full smoke/flame rerun

On user request, `rerun_visual.py` reproduced `confirm20_ACG_3200_s4321` locally with the native solver and four OpenMP threads. The original generated deck hash was checked against the archived cloud run before enabling SMOKE3D, 0.5-second smoke/particle output and displaying all vegetation particles. No ember-generation physics was added: reddish dots in the earlier view are the BROWN wood particle classes, not embers or temperature-coded flames. FDS source `part.f90:INITIALIZE_SINGLE_PARTICLE` confirms SAMPLING_FACTOR controls particle SHOW flags.

The 90-second rerun took 333.94 wall seconds and incurred $0 cloud cost. `verify_full_visual.py` confirms first device burning at 9.5052105 s, and fds2ascii checks all six house boundary orientations: maximum patch-average burning rate over 0–90 s is 0.010302 kg/m²/s (513 samples), matching the original aggregate result. Different binaries are recorded in provenance; this is not a claim that every flow-field value is identical.

Outputs: `results/full_visual/smoke_flame.gif` and `results/full_visual/three_views.gif`. The latter compares smoke/flames against nearest available original temperature frames and the static final graph state. Flames visualize HRRPUV, smoke visualizes soot. The graph has no physical clock. No flying embers are simulated in this scene. Reproduce with DVC stages `full_visual_solve` and `full_visual_render`; raw data and rendering work are preserved separately.
