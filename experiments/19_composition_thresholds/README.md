# Composition with verified ignition coverage

Status: campaign stopped after 11 new full-horizon simulations because validation layout AD had no positive endpoint at powers up to 3200 kW. Cloud cleanup verified zero VMs, disks and jobs. Estimated compute $0.0765; with the full ancillary allowance, $0.1765 (not an invoice). No new three-crown calibration or confirmation runs were performed; no models were fitted.

## Verified partial outcome

Local extraction cross-checked all 44 available development records against raw six-face structure burning-rate boundary data through fds2ascii over 0–90 s. Training now contains 11 ignitions / 36 cases. Validation AC contains 1 ignition / 4 cases (new 1700 kW case ignited); AD contains 0 / 4 (835, 1700, 2400, 3200 kW). Thus validation collectively contains both outcomes, but the preregistered per-layout coverage gate fails for AD. The process stopped before testing composition. Existing data is retained for reuse; no automatic extension or retry was launched.

## What failed and what changes

Experiment 18 completed, but raw structure burning-rate extraction showed no ignition in all six validation and all twelve test cases. It therefore could not test ignition classification across the boundary. Its completed data, pinned particle-vegetation model, full 0.5 m mesh, structure, 90 s horizon, source timing, Docker image and model architectures are reused. We do not rerun the original grid or change the structure ignition rule.

The correction is to acquire supported source ranges and require class coverage explicitly. Calibration on AB alone no longer selects the three-crown exposure range. The old three-crown outcomes are now calibration evidence and never counted as fresh test results.

## Reuse and new-run allocation

| Purpose | Reused runs | New runs |
|---|---:|---:|
| Training: original 24 plus six AB calibration cases | 30 | 6 |
| Validation AC; new validation layout AD replaces BD | 3 | 3–7 |
| Threshold search for ABC, ABD, ACD | 3 negative endpoints | 6–12 |
| Fresh confirmation: 3 layouts x 2 powers x 2 FDS seeds | 0 | 12 |
| Total | 36 | 27–37 |

All reused raw output is available in data/reused-evidence.tar.gz, tracked as an external DVC input; design.json records selected case/deck hashes and roles. Unselected old runs remain in the provenance archive but cannot enter the new training/validation/test datasets.

Training additions: total source power 3200 kW for A, B, C, D and CD; A at 300 kW. AB at 3200 kW already exists. These additions extend both total-source and per-crown source support; all later confirmation inputs must fall inside those training ranges. Total source power continues to be divided equally among active crowns. Wind, fuel parameters, moisture, building material and geometry remain unchanged.

Validation: reuse the three known AC negatives, then try total powers 1700, 2400, 3200 kW until the first positive. For AD, first run 835 kW as a low endpoint, then the same upper ladder. Require both labels separately in AC and AD. An unexpectedly positive low endpoint or missing positive at 3200 kW stops acquisition, rather than proceeding with unusable validation. BD is deliberately excluded because its remote-fuel configuration did not exercise the desired near-wall ignition boundary; this narrows the scope.

Three-crown calibration: for ABC, ABD and ACD, reuse the old 1252.5 kW negative at seed 1234. Try 2000, 2600, 3200 kW in order until a positive is found; each negative replaces the low endpoint. Run one midpoint to narrow the observed bracket. These observations are acquisition-only and cannot train, tune or score a model. The bracket describes observed endpoints; monotonic ignition over every intervening power is not assumed.

Confirmation: for each bracket [L,H], choose total powers 0.8 L and min(3200, 1.2 H), then run both at fresh FDS seeds 4321 and 5678. Margins reduce sensitivity to a small random-seed shift around the crossing. Preserve every confirmation outcome; never discard a missed class or extend the range after scoring. Each layout must contain both labels across its four confirmations, and the entire set must contain at least four positive and four negative cases. If the gate fails, report coverage failure and do not claim a composition result. No bounded run can guarantee what the physics will do; the gate guarantees an all-negative dataset cannot masquerade as a successful test.

The final layouts all contain the nearest-wall crown A. BCD remains a historical negative control outside the confirmatory scope. The result concerns composition across these arrangements, not arbitrary lots, all distances or unseen vegetation species.

## Preventing leakage and misleading scores

The acquisition algorithm and model settings are fixed before new simulation results. Training and epoch selection read only the designated one-/two-crown records. Epoch selection uses class-balanced Brier score averaged equally over the two validation layouts; no positive-free validation split is allowed. Retain the prior five model-training seeds and architectures. Newly acquired three-crown data must never affect training, model selection or feature normalization.

Save immutable trained weights and their hashes before loading the adaptively selected confirmation inputs. Then generate and freeze predictions from those inputs before opening their FDS outputs. Adaptive bracket metadata is not a model feature. This ordering is enforced in separate pipeline stages, with prediction hashes recorded before scoring. The cloud can produce all outputs in one bounded job; local analysis opens development evidence first and final confirmation evidence only after prediction freezing.

Compare the interaction graph, matched-size additive model without crown-to-crown communication, and simple aggregate-feature predictor. Also report an always-negative baseline explicitly. Primary metrics are false negatives, false positives, balanced accuracy and Brier score on the fixed confirmation set, averaged by layout with every training seed shown. Report continuous face-temperature errors as secondary evidence. A provisional promising result retains the prior screen: at least 10/12 correct, at most one false negative, and at least 20% Brier improvement over both learned baselines in at least four of five training seeds. Both class-coverage gates must pass first. Three geometries with repeated seeds are not twelve independent layouts; this remains a feasibility screen. Since the test is deliberately selected around ignition brackets, its class proportions and probability scores do not estimate population wildfire risk or probability calibration.

Before training/scoring, independently verify labels from the raw structure burning-rate boundaries through fds2ascii and cross-check device labels. Incomplete solver runs are missing evidence, never negatives. Retain prior numerical tolerances, and report discrepancies rather than silently choosing one label.

## Incremental cost before launch

Expected 27–33 new cases, maximum 37. Prior runtime was about 4.27 hours for 48 cases; higher-power examples took roughly 320–407 s each. Allow 3–4.5 worker hours including overhead: $0.197–$0.296 Spot compute, plus $0.10 ancillary allowance, or approximately $0.30–$0.40 incremental total. Existing cloud artifacts and image are reused; no image build, GPU, automatic retry or on-demand fallback. Training stays local.

Proposed controller deadline: five hours. At $0.065744/hour for c3-standard-4 in Iowa, deadline compute plus the full ancillary allowance is $0.429; reserve $0.45 including rounding/cleanup contingency. This is a runtime-bound estimate, not a guaranteed billing cap. A slower or interrupted campaign stops incomplete; it does not extend its allowance. Check pricing again immediately before launch. Official price source: https://cloud.google.com/spot-vms/pricing?hl=en .

## Implemented preparation

acquisition.py contains the bounded adaptive policy and mandatory coverage gates. It accepts an execution adapter; its self-test uses synthetic outcome functions and cannot invoke FDS or Google Cloud. Tests cover the successful balanced path, the exact worst-case 37-run ceiling, failure to find ignition, an unexpectedly igniting low endpoint, incomplete solver output, and an all-negative confirmation set. verify_reuse.py checks selected archived completion/deck hashes. Pinned generator and model definitions are copied locally. These preparation checks are recorded in dvc.yaml/dvc.lock. Cloud orchestration, variable-sized extraction/training, immutable checkpoint/prediction handling and final scoring are now wired. Synthetic integration checks passed for fit/freeze/predict/score ordering and rejection of an all-negative confirmation set. Native local FDS initialization passed for A, AD and ABC at 3200 kW total source power. No result from experiment 18 is overwritten.


`finish.py` waits only for this execution, verifies cloud cleanup, then automatically downloads and analyzes the evidence locally. It never starts or retries cloud compute. Local analysis requires the laptop to be awake; the five-hour cloud cleanup controller is independent of it.
