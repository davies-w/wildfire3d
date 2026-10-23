# Attempt 10: fixed U-Net continuous-field fitting

This implements the first milestone of the 23 October research review: establish meaningful fitting before expanding data or claiming a learned burning simulator. It does not modify the ten independent HOT classifiers.

## Design frozen before submission

Two fresh models use the attempt07 spatial U-Net blocks, widths, skip connections and up/downsampling. Input/output layers change to 14 inputs and six continuous outputs. Inputs are four initial fuel-density maps, xyz coordinates, wind, moisture, loading, crown height, sine/cosine ignition angle, and actual time scaled to [-1,1]. There are no truth-field inputs. Both arms start with identical weights and independent AdamW optimizers:

- `single`: all 91 frames of x32_033_s0.
- `eight`: all 91 frames of each of the same eight previously selected TRAIN configurations, two per strength band.

This is a conditions-plus-time diagnostic, not state evolution or recurrence. Every complete epoch visits every training frame once, shuffled without replacement. It runs both arms in alternating epochs so a deadline does not starve the second arm. Full training and all 32 existing development-validation configurations (40 trajectories including replicas) are evaluated every epoch. Replicas are averaged within configuration. No test data are used; this development set has been examined previously and is not pristine.

## Objective and physical checks

Outputs are raw encoded temperature, volumetric heat release, u/v/w and integrated radiation intensity. Encoding and the original eight-training-case standard deviations (floor 0.05) are fixed; no validation normalization is fitted. The single-case arm also uses those disclosed eight-case scales.

The one fixed objective is normalized squared error averaged equally across six channels. Within each frame, the temperature and heat-release channel errors are averaged equally between truth-active and truth-inactive regions (T>50°C and HRR>0.01 kW/m³). If one region is absent, ordinary whole-volume MSE is used. Other channels use whole-volume MSE. There are no additional auxiliary losses and no weighting sweep. Squared rather than absolute error and spatial region balance explicitly change the old regression objective; this run does not isolate every difference from the old decoder. It tests whether this declared spatial regression setup can fit physical fields.

There is no output clamp before training loss. Bounds apply only when decoding reported physical fields. Report physical errors alongside raw encoded objectives, whole-volume errors, hot/burning-region errors, total gas-HRR histories and energy, HOT precision/recall/F1, and negative/upper-clipped HRR fractions. Radiation is gas integrated intensity, not surface heat flux.

Final training fit and validation selection are separate results. Select the minimum configuration-balanced validation whole-history objective checkpoint, but retain every epoch and the final checkpoint. Diagnostic fit gates are reported for both final and selected checkpoints, on each trained case after the igniter: hot-region temperature relative L1 <=20%, burning-region HRR relative L1 <=30%, and total-HRR relative L1 <=20%. These are predeclared engineering checks, not physical-validation standards. Undefined denominators do not count as success. An improved aggregate objective alone never authorizes data expansion.

## Optimization, deadlines and preservation

Constant learning rate 3e-4, batch size 4, up to 200 epochs per arm. After epoch50, compare consecutive disjoint ten-epoch means of train and validation post-source objective, hot-temperature relative L1 and total-HRR relative L1. Three successive checks below 1% relative change or 1e-4 absolute change establish only an empirical plateau. Epoch limits, low errors on cold fields and time limits are not convergence.

Estimated runtime is approximately 1–3 hours after allocation; full-field validation may dominate and the estimate is uncertain. Cloud limits: 20-minute allocation queue, three-hour task, 3h05 VM age, 3h30 absolute workflow limit, 2h45 worker soft limit. No automatic paid retry. Checkpoints every epoch and 250 optimizer updates include optimizer, RNG, shuffle position, partial loss aggregate, validation-selection state and learning history. Separate reserved continuation is required if interrupted.

Full allowance is $7 before any upload/submission: $3.20 compute and $3.80 ancillary/transfer/cleanup. This would bring cumulative retained reservations from $109.10 to $116.10 of the authorized $125; failures are retained and invoices remain unknown. The launcher refuses duplicate/unknown submissions. One locked collector verifies VM/job/disk cleanup and removes the exact temporary input-object grant.

Original raw archives are SHA256-verified, decoded locally without training, and packed into a fresh input object so expired GCS inputs cannot break the run. CPU preflight checks metric arithmetic, region balance, nonzero negative-HRR gradients, split separation, whole-grid shape and inference serialization. Actual CUDA gradient and serialization checks must pass before training. All source/workflow generators, results and DVC metadata are committed; inputs/checkpoints/data are preserved through the approved public Hugging Face DVC archive.

## Scope

Generic 3m-wide conical crowns, heights4/6/8/10m above a2m base, 1600 weighted particles, 0.5m grid and24×16×16m domain,180s histories, imposed1500°C ignition for20s. No trunks, buildings or embers. These six gas fields do not include solid-ground temperature or a separately evolving fuel/water/char state. Successful fitting would be a representation diagnostic, not generalization to realistic trees or replacement of FDS.
