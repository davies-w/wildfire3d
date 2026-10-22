# Composition pilot — pre-run design

Status: complete. All 48 simulations reached their full horizon; cloud cleanup confirmed zero VMs, disks and jobs. Estimated compute cost $0.281; including the full $0.10 ancillary allowance, $0.381 (invoice not confirmed). Local analysis initially stopped on a Git-ignore/DVC metadata error; that was repaired, and extraction, training, frozen prediction and held-out evaluation then completed. DVC is up to date.

## Outcome

The composition test is inconclusive. Training had 6 ignitions in 24 cases, validation had 0 in 6, and the held-out three-crown test had 0 in 12. All three model types classified every test case as non-igniting. The interaction model therefore demonstrated no useful advantage over the additive model or an always-negative classifier. Validation containing only negative cases also makes model selection weak. These results do not establish calibrated probabilities or generalization across the ignition boundary.

The single two-crown calibration did not provide threshold coverage for the held-out configurations when total burner power was shared across more crowns. That is a design-coverage failure; it does not show that compositional learning is impossible. A follow-up must establish both outcome classes across development layouts and independently bracket the exposure range for a separate three-crown calibration layout before locking new test layouts. Its training power range must cover the test power range. No follow-up cloud runs have been launched.

Primary labels were cross-checked against raw six-face FDS burning-rate boundary data through fds2ascii for all 42 development/test cases. Full scores and evidence are in results/evaluation.json, data/development.json and data/test.json.

## Question

Can a shared interaction network trained on one- and two-crown scenes predict structure ignition in previously unseen three-crown arrangements, better than models that ignore interactions? This is a small falsifiable feasibility test, not proof of real-property accuracy. A negative result can also reflect inadequate data or representation.

## Fixed scene

Reuse experiment 17 full 24 x 24 x 12 m domain, uniform 0.5 m cells (55,296 total), pinned FDS image, 90 s horizon, 3 m/s wind from 270 degrees, synthetic structure at x=14..20,y=10..14,z=0..4. Use the same stationary Douglas-fir foliage and three roundwood particle classes, 14% moisture, crown height 1.96 m, radius 0.85 m and base 0.15 m. No block vegetation and no embers. Structure material and 350 C prescribed ignition remain synthetic; no claim of real ignition validation or mesh convergence.

Four candidate crown centers: A=(12,12), B=(10,10), C=(10,14), D=(8,12). All are in the full fine domain and crowns do not overlap. Use one 1 m2 ground burner beneath each active crown, with the previous 30 s exposure ramp. Total burner power is divided by the crown count, preventing a trivial increase in external ignition power with object count. Total vegetation mass still increases and is explicitly supplied to the baseline. This tests interacting burning fuel regions, not unassisted spread from a single ignition point.

## Run allocation (maximum 48)

- Calibration: at most six full runs on training layout AB. Start total source powers at 200 and 3200 kW. If they do not bracket ignition/non-ignition, stop as inconclusive without an automatic expansion. Use remaining four runs to bisect; report actual bracket width. Define P0 as the midpoint. This calibration may not yield a tight bracket.
- Training: six layouts A, B, C, D, AB, CD, each at total powers 0.65, 0.9, 1.1, 1.5 times P0: 24 runs.
- Validation: AC and BD, each at 0.8, 1.0, 1.2 times P0: six runs.
- Locked test: ABC, ABD, ACD, BCD, each at 0.8, 1.0, 1.2 times P0: 12 runs.

Calibration observations can inform scale selection and belong to development data, never test data. No test temperatures, labels or fitted statistics enter training, normalization, stopping or model selection. All snapshots and patches from one layout stay in its split. Freeze predictions before inspecting test outputs. If the test fails to include both ignition and non-ignition, report inadequate threshold coverage; do not select new test cases after seeing outcomes and call that the same test.

## Prediction and models

Input is initial geometry, material/fuel descriptors, source power and fixed conditions. No solver-derived input at inference. Predict whether any structure surface ignites within 90 s. Use a direct network, not an autoregressive time-step simulator.

Use a deliberately small shared graph network: one node per crown and fixed structure face patches, geometric pair features (relative displacement, distance, orientation, wind alignment), two message-passing layers, shared width 8, and a pooled structure output. Include burner positions/powers as source features. The 1,174 parameter model is capacity-limited and regularized. Initial physical feature scaling is fixed or fitted to training only. Select epochs using validation only; run five training seeds and report all, not the best test seed.

Compare (1) a shared per-crown encoder with additive pooling and no crown-to-crown messages, using comparable parameter count; (2) a regularized simple model using total source power, fuel mass, nearest gap and summed distance/wind exposure features. Both receive the same training data. The interaction ablation is essential: otherwise good predictions do not demonstrate useful learned communication.

Provide auxiliary supervision from face temperature and heat-flux histories and ignition times, using a fixed set of output times. Auxiliary samples are correlated and do not inflate independent scene count. Whole-structure ignition is the primary endpoint. Time-to-ignition is censored at 90 s, not encoded as zero or as ignition at 90 s. Noncompleted runs are missing data, never negative labels.

## Evidence and decision

Extract all six structure faces' burning-rate and temperature boundary data with fds2ascii; cross-check device-based labels before scoring. Preserve raw boundary data and actual aggregate CPU/wall time. Define ignition as positive burning-rate output above an explicitly recorded numerical tolerance and validate against the synthetic prescribed ignition rule. Do not assume a temperature sample below threshold proves no ignition between samples.

Report per-case frozen predictions, classification errors (especially false negatives), Brier scores, auxiliary temperature errors, all training seeds, and timing for inference alone and geometry preprocessing separately. Four held-out layouts are too few to establish calibrated probabilities or tight confidence bounds.

Provisional continuation criterion: at least 10/12 correct test outcomes, no more than one missed ignition, and at least 20% lower mean Brier score than both baselines, with the improvement present in at least four of five training seeds. These are engineering screening criteria, not statistical significance. If all models perform similarly, learned interactions have not earned their complexity. If outcomes lack both classes or all baselines are already nearly perfect, the experiment is inconclusive about composition. Learning-curve and training-fit diagnostics distinguish clear underfitting from failure to transfer.

## Cost and execution controls to implement before launch

One c3-standard-4 Spot worker in us-central1; existing image; no build, GPU, retry or on-demand fallback. Training runs locally on CPU. Prior matched full-reference cases took about five wall minutes; 48 cases imply about four worker hours, with a five-hour total controller deadline allowing for overhead and heavier three-crown cases. At $0.065744/hour, compute is $0.263–$0.329; add $0.10 ancillary allowance: $0.363–$0.429. Reserve $0.45 including rounding/cleanup contingency. Recheck rate before launch. This is not a guaranteed billing cap. A five-hour stop may leave the dataset incomplete; do not extend automatically.

Implement worker stop before the controller deadline and leave cleanup time; stop scheduling new cases if remaining time cannot accommodate one. Reuse tested cleanup controller, verify no surviving VMs/disks/jobs after termination. Archive outputs within ancillary allowance. No automatic cloud launch from dvc repro: paid execution remains explicit. Before execution, copy pinned model inputs into this experiment, generate decks, validate local startup and mesh/geometry invariants, implement extraction/training/evaluation as DVC stages, and hash frozen configuration and splits. Completed evidence and dvc.lock will accompany results.

## Implementation details frozen before launch

Five exposed structure-face patches supply auxiliary targets; the buried bottom face is excluded from the network. Primary ignition still uses the entire structure, with six-face raw-boundary extraction. The graph and additive model each have 1,174 parameters; the simple linear baseline has 620 including its auxiliary prediction heads. Both neural models use two layers of width eight. The additive model prevents messages into crown nodes and between face nodes; its independently encoded crowns contribute summed messages to surfaces. Material and moisture are fixed features in this pilot.

Local FDS initialization ran to 1.05 simulated seconds for D, AB, and ACD; checked mesh alignment, finite face-device output and positive vegetation mass. Synthetic model checks verify finite gradients and invariance to crown ordering; these are implementation checks, not predictive findings.

Run commands: `python prepare_cloud.py`, `python cloud.py deploy`, then the explicitly authorized `python cloud.py launch`. `python finish.py` waits for this execution only, verifies cleanup, downloads evidence, and runs local extraction/training/evaluation. It never launches or retries a cloud job. If the laptop sleeps, cloud shutdown still operates; local analysis waits for the laptop to resume.
