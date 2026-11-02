# Fresh four-state + hot-gas-cone model (rotation 0)

Use experiment 39's architecture, **not its checkpoint**: fresh seed3516, empty AdamW, one GRU64 with eight four-state history samples and nine external inputs, shared Linear64+SiLU, no dropout. Retain four delta outputs and three internal gates; add one cone-presence logit and five cone readouts (25,549 parameters total). Cone truth and predictions are **not recurrent inputs**. The new readouts share the learned memory with the original task. Fresh optimization and the added objective mean comparisons with the continued experiment39 cannot isolate a single cause.

Frozen split: 1,662 train / 210 validation / 208 test histories, disjoint configurations. Curriculum windows 1/8/16/32/64/90 begin at epochs1/21/41/61/110/130. Minimum160, maximum400, patience30 after the final stage. Full90 means90 prediction steps, approximately180 seconds, and gives seven optimizer updates/epoch versus176 at64, so epoch counts do not represent equal optimization exposure. AdamW LR3e-4, weight decay1e-4, clip1, batch256. No local optimizer or neural training.

## Exact combined objective

For each training window:

`L = L_state + 0.1 L_gate + 0.1 L_presence + 1.0 L_cone`

- `L_state` is unchanged: integrate the absolute piecewise-linear prediction error over elapsed physical time for each of water, fuel, gas and heating; divide by window duration and that history's full reference feature range; average the four features. The crossing-zero interval integral is exact for the piecewise-linear error. This uses the existing per-history normalization policy, not predicted ranges.
- `L_gate` is the existing elapsed-time-weighted supervised BCE on the three internal gates.
- `L_presence` is BCE on the new presence logit, elapsed-time weighted over all predicted endpoints, divided by window duration. Presence means at least one reference cell above50°C, not flame or ignition.
- `L_cone` is the elapsed-time-weighted **mean of five normalized SmoothL1 errors**, divided by total reference-active elapsed time in the window. All-inactive windows contribute zero. Mask using reference activity, never predicted presence; inactive placeholders cannot enter regression. Endpoint weights are the preceding interval duration; this is not an exact geometric error integral between snapshots.

For parameter residual `e=(prediction-reference)/scale`, SmoothL1 with beta0.1 is `e²/(2×0.1)` when `|e|<0.1`, otherwise `|e|−0.05`. Fixed scales, in parameter order, are **12m pivot height,90° tilt,24m axial length,16m end radius,1500°C peak temperature**. These are unit scales, not output clipping thresholds or fitted validation statistics. Cone output height is bounded0–12m, tilt0–90°; length/radius are positive; active peak temperature is above50°C. Regression targets include the previously disclosed degenerate sub-cell fits, without silently removing them.

The weights1/0.1/0.1/1 are a first experimental choice, not proven optimal. Each block is separately reported. Windows have inverse-replica weighting as before; validation scores average histories within physical configuration then give configurations equal weight. **Selection uses full-rollout validation `L_state + 0.1 L_presence + L_cone`**, excluding the old auxiliary gate BCE. This deliberately changes selection from experiment39; original four-state integral scores remain separately visible. No test score may affect training, scaling, selection or patience. A selection-freeze artifact precedes final test evaluation.

## Cone labels and limits

Reuse the fully verified1662 training histories from experiment44. Extract210 validation and208 test labels using the identical fixed geometric rule; reading reference labels is not test prediction evaluation. All2080 source/time mappings are checked. Frame0 initializes the four observed states; cone predictions/loss cover the90 future endpoints.

These are instantaneous saved gas temperatures about2s apart, not interval maxima, heat flux or heat dose. Cones enclose95% of >50°C cell centres with a fixed downwind+x/verticalz axis and apex on the tree centreline. The coarse fit uses ground or seven crown apex heights and10° angle steps. Training cones have median20.5% purity;86.8% use a ground apex;2.71% have sub-0.5m axial lengths. They are loose geometric labels, not physical flame-pivot measurements. Gas includes the imposed1500°C source during20s. Generic4–10m vegetation crowns,0.5m grid,24×16×16m observed crop; no buildings, trunks, embers, receiver heating or ignition claims. The dataset has been examined in earlier experiments; it is not pristine confirmation.

The results gallery will keep the four state charts and add **one fifth chart**: cone length on the left axis (m), maximum temperature inside the cone on the right (°C), reference solid/prediction dashed, absent cones shown as gaps. This chart cannot reveal every pivot, tilt or width error; those need geometry/storyboard inspection.

## Cloud execution and recovery

One guarded Google Cloud Workflow races three ownership-gated n1-standard-4 + one **Spot T4** queues in Oregon(us-west1), Iowa(us-central1), South Carolina(us-east1). The first running VM wins; losing jobs/VMs/disks must be verified absent before the ownership grant permits optimizer probes or training. No allocation deadline or automatic Batch retry. Soft training deadline10.5h, task10.75h, VM11h; these are safety bounds, not a runtime forecast. Earlier comparable runs took hours; the actual new-loss timing is measured on the winning T4 before fitting and retained as advisory evidence.

Every completed epoch preserves model, optimizer, RNG, history and best-selection state. A partial epoch can be lost. An eviction requires diagnosis, complete artifact collection, cleanup and measured-cost reconciliation before any uniquely identified checkpoint continuation; never blindly rerun launch or an old queue. Spending remains bounded by the existing private cumulative ledger. No ledger or credentials are public.

Mandatory cloud proofs: actual T4; all six horizons actual combined-loss backward including nonzero gradients for all six cone outputs; synthetic nonempty optimizer/RNG next-update replay; exact fresh epoch1 first-batch replay; deterministic serialization/CUDA prefix checks; evaluation and transport checks; actual first-epoch checkpoint replay. Probe weights are discarded. CPU `validate.py` and loss tests do not substitute for these proofs.

## Commands

Run `prepare_labels.py`, `prepare.py`, forward-only `validate.py` and `test_joint_objective.py`, then guarded `build_pool.py`, `deploy.py`, and **launch.py exactly once**. `monitor.py` is read-only. `fetch_progress.py or|ia|sc` verifies completed epoch records and checkpoint metadata; `audit_startup.py` verifies seven startup proofs. `collect.py` requires actual Batch success, pinned hashes and selection-before-test evidence; `close.py` requires collection and measured allocation reconciliation before removing the exact read grant or releasing reservations.

DVC stages and `preserve_artifacts.py STAGE` use direct `scripts/dvc_hf.py` upload with remote verification; no cache/local mirror. Git source, documentation, validation and DVC hashes are public. Raw cloud orchestration and financial records remain private; scientific snapshots and eventual collected models are uploaded separately.


## Pool01 controller failure and pool02 repair

Pool01 failed before ownership or training: workflow step `inventory.get_disks` returned `ConnectionError: connection broken` while verifying loser cleanup. This was a transient controller read failure, not a model failure or Spot eviction. Original objects were privately archived with generation/MD5/SHA checks; no ownership grant or epoch existed. All jobs/VMs/disks were verified absent and the exact grant/reservations closed after allocation accounting. Raw operational failure records remain private; `failure01-summary.json` is the sanitized public account.

Pool02 has new workflow/job IDs and prefix, with byte-identical scientific model, worker, labels and optimizer recipe. It adds bounded `http.default_retry` to GET/DELETE calls, including calls within existing404 handlers. Job-creation POSTs are not blindly retried. See [Google's idempotent retry policy](https://docs.cloud.google.com/workflows/docs/reference/stdlib/http/default_retry). Current launch tools are `prepare02.py`, `build_pool02.py`, `deploy02.py`, `launch02.py`; current monitor/collector/audit helpers target02, original helpers are retained as `*01.py`. Never rerun original launch/build/deploy after intent. The loss and fresh-weight design are unchanged.

## Stopped by user

This run was stopped at108 completed epochs because the cone values were output-only rather than recurrent inputs. This was an implementation mismatch, not the requested design. All completed checkpoints are preserved separately. Experiment46 corrects the input to eight ten-value states and starts fresh; this run must not restart.
