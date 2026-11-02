# Eight historical timesteps, ten recurrent state values

This corrects the design error in experiment45, which treated the cone values as output-only. The user stopped that run. Experiment46 starts from fresh seed3516 weights and an empty optimizer; no model, checkpoint or epochs from45 are reused.

Each of eight history entries contains ten values: water, fuel, gas, heating, cone-presence probability, pivot height, tilt from vertical, axial length, end radius, and peak temperature inside the cone. The GRU receives the flattened8×10 history plus nine external inputs: **89 inputs, one64-unit recurrent layer**, sharedLinear64+SiLU, no dropout, four physical deltas/three internal gates and six cone outputs. Total34,765 parameters. ALL TEN predicted values are appended to history during autonomous training and evaluation. Cone truth is used only in observed history through the forecast origin; never after it. The detached teacher-prefix memory follows that same restriction.

The original four states keep their train-only asinh normalization. Cone presence is0/1 in reference history and a soft probability in predicted history. The five cone values use fixed scales12m/90°/24m/16m/1500°C. Inactive reference geometry is zero (undefined geometry convention); predicted geometry remains available alongside predicted presence, without thresholding or silently replacing it with truth. Presence loss teaches absence. The model has no receiver/target inputs.

## Unchanged curriculum and loss

Windows1→8→16→32→64→90 begin at epochs1/21/41/61/110/130. Minimum160, maximum400, patience30 after the final stage. Full90 is approximately180seconds, not90seconds; seven updates/epoch versus176 at64, so epoch counts do not measure equal optimizer exposure. Frozen rotation0:1662train/210validation/208test histories,204test configurations. AdamW LR3e-4, weight decay1e-4, clip1, batch256.

Training loss = four-state range-normalized absolute integral +0.1 original gateBCE +0.1 cone-presenceBCE +1.0 cone-parameter loss. The cone term is the mean of five normalized SmoothL1(beta0.1) errors, weighted by elapsed time and normalized by reference-active duration. All-inactive windows contribute zero; the reference mask, never predicted presence, controls regression. Presence is scored at all endpoints. These are initial experimental weights. Cone errors compare saved endpoints, not exact between-frame geometric integrals. Validation selection is state integral +0.1 presenceBCE +cone term; old gateBCE excluded, all blocks reported separately. Test evaluation occurs only after selection freezes.

## Evidence and limitations

Forward-only validation checks all48 additional cone history fields affect memory, ten-value feedback at every autonomous step, observed-only prefix, serialization, disjoint configurations and actual loss at all six horizons. No local optimizer/backward/training is run. On the winning T4, mandatory checks repeat actual six-horizon backward, gradients in all cone-history inputs and cone outputs, exact fresh first-batch optimizer/RNG replay, nonempty optimizer replay, and actual epoch1 checkpoint replay. Zero-initialized readout weights initially block gradients to the GRU, so the gradient-path probe uses temporary nonzero cone readout weights; the exact fresh first-batch replay still uses the actual zero-head initialization. Probe weights are discarded. Every completed epoch uploads a full model/optimizer/RNG/history checkpoint; an unfinished epoch can be lost.

Labels are the same2080 verified histories extracted in45. They describe broad95%-recall envelopes of >50°C gas cell centres, not physical flame boundaries or ignition. Training median cone purity is about20.5%;86.8% use a ground apex and2.71% have sub-0.5m lengths. The fixed+x/downwind plane and sampled apex/angle grid constrain fits. Saved peak temperatures approximately2s apart are instantaneous, not interval peaks, heat flux or heat dose. Generic4–10m crowns,0.5m mesh,24×16×16m observed crop; imposed1500°C ignition source for20s is included; no buildings, trunks or embers. Historical dataset, not pristine validation. The fifth results chart shows length and peak temperature; it does not capture pivot/tilt/radius errors.

## Execution and preservation

One Google Cloud controller races three SpotT4 candidates in Oregon/Iowa/South Carolina. Only the ownership-granted winner may run optimizer probes, after verified loser cleanup. No allocation deadline; zero automatic Batch retries; soft10.5h/task10.75h/VM11h limits. GET/DELETE use bounded retries, creationPOST does not. Private cumulative spending ledger is checked before any launch. Never rerun prepare/build/deploy/launch after submission intent. No old queues are restarted.

`prepare.py`, forward-only `validate.py`, `build_pool.py`, `deploy.py`, then guarded `launch.py` exactly once. `monitor.py`, `fetch_progress.py`, `audit_startup.py` and `verify_ownership.py` only inspect evidence. `collect.py` requires actual Batch success and complete verified artifacts; `close.py` additionally requires measured allocation reconciliation before grant/reservation removal.

DVC preservation uses direct `scripts/dvc_hf.py` with hashes/readback, without local cache or mirror. Only models, datasets, training results and reviewed source are public; spending records, credentials and raw operational archives remain private. Git source/docs/DVC hashes are committed and pushed. Old experiment45 checkpoints are preserved separately and never used as initialization.

## Pool01 interruption

Google Cloud preempted the winning Iowa Spot VM after epoch116. All116 completed checkpoints, including optimizer/RNG/history, are preserved and uploaded with verified hashes. All three candidate resource inventories are empty; the exact read grant and reservations were closed after runtime reconciliation. Recovery must resume epoch117 with64-step windows from checkpoint116; Pool02 was submitted once at2026-11-02T16:27:02Z, execution75f2fc9f-2401-48eb-9be9-a1fac640a5d0. It resumes epoch117 with64-step windows, with the unchanged130 full90 transition and selection/patience history. Actual resumed training requires epoch117 plus its checkpoint and seven cloud startup proofs.

## Pool02 pre-training eviction and pool03

Pool02 was preempted before its worker started (Batch exit50001), with no new epochs. All15 cloud objects are privately archived and hashed; jobs/VMs/disks are empty, and its exact read grant and reservations are closed after runtime audit. Pool03 uses byte-identical model/data/checkpoint files and was submitted once at 2026-11-02T16:43:09.566840803Z (execution d2ae05ca-7096-411b-b95c-c5a3384721f0). It resumes epoch117 from116; the original curriculum and optimizer/RNG/selection history are unchanged. Actual resumed training remains unverified until a completed117 checkpoint and the cloud startup proofs are checked.

## Completed result

Batch succeeded after164 epochs; validation selected134 before test evaluation. All164 model/optimizer/RNG checkpoints and the exact208 test histories/204 configurations were collected with SHA/MD5/generation verification. Pool03 jobs/VMs/disks are empty; its exact read grant and reservations were closed after allocation-runtime reconciliation.

Selected four-state test integral error is5.0073%, versus4.7861% for experiment39. Water is worse; fuel/gas/heating slightly better. The cone active-reference MAEs are0.319m pivot,6.871degrees tilt,1.466m length,0.759m radius and86.531°C peak temperature. Presence accuracy97.31%, missed-active3.67%, false-active2.16%. These compare to broad fitted hot-gas envelopes, not physical flame boundaries or heat received. The comparison is exploratory on historically examined data and differs in fresh/continued optimization and selection objective.

Report: https://wdavies-fire-reports.static.hf.space/cone46/index.html
Gallery: https://wdavies-fire-reports.static.hf.space/full-sequence/cone46-r0.html

## Random held-out 3D animations

[Watch two random test histories](https://wdavies-fire-reports.static.hf.space/cone46/animations/index.html). Uniform NumPy seed20261102 draw without replacement selected IDs1498 and1598 (x36_0978_s0 and x36_1078_s0), with no error/appearance filtering. Both have8m crowns above2m,3m diameter; winds4 and3m/s. Each GIF includes all91 saved frames over approximately180s at8fps (about16x playback). Actual >50°C gas cell-centre temperatures appear in both panels, display-subsampled to at most600 cells including the hottest. Only the cone in the right panel is predicted; no predicted full temperature field or heat flux is invented. Cyan/magenta are reference/predicted wire envelopes; green is fixed crown geometry, not a fuel-state estimate. Imposed ignition during0–20s is included. No new simulation or neural training was run.

The animations use one fixed mean-centred colour scale shared across both histories:123.656–136.673°C, centred130.164°C (mean±5% in °C of all >50°C cell observations, before display subsampling). Values outside it saturate only in colour; source/model temperatures are unchanged. One fixed GIF palette prevents per-frame colour quantization drift; the legend region was verified pixel-identical in all91 decoded frames of both GIFs.
