# Recorded-condition HOT gas comparison

Interactive JavaScript viewer for all 472 new-geometry archived trajectories, pooling training, validation and previously examined test cases. Sliders select crown height, moisture, fuel loading, wind speed and ignition angle; seed distinguishes repeated runs. A sixth slider selects one of ten independent models (0,20,...180 seconds). Unrecorded combinations remain empty. No nearest-case substitution is made.

Truth and prediction use 48×32×32 gas cells (0.5m resolution, 24×16×16m). HOT means gas temperature >50°C. Orange boxes are thresholded gas cells, not flame surfaces. The optional initial-fuel cells are not solid trees. Camera rotation, pan and zoom are synchronized between views.

## Data and inference

The 472 runs comprise 360 fitted primary training runs, 24 additional training seeds, 40 validation trajectories (32 configurations), and 48 previously examined test trajectories. Older legacy geometry is excluded. Test results are not pristine generalization evidence. Models were frozen at their prescribed final epochs before adding viewer cases; no model selection or fitting uses these extra cases.

`prepare_viewer_inputs.py` verifies archived raw and deck SHA256 hashes and freezes ten final checkpoints. `predict_viewer.py` performs CPU inference only, with the original training density normalization and 13 inputs. Outputs are precomputed per recorded configuration: this is not arbitrary-parameter browser inference. Each selected snapshot displays its actual saved timestamp, which may differ slightly from the nominal model time.

Five nontrivial models (20–100s) reached 300 epochs without meeting the preset plateau rule. All-cold training times (0 and120–180s) met that empirical rule at200 epochs. Neither a cap nor an all-cold solution establishes useful burning fidelity. Undefined precision/recall is displayed explicitly.

## Run

From the repository root, serve this directory with Python's HTTP server and open `/viewer/`. The viewer has pinned local Three.js 0.160.1 assets and its license; it needs no CDN. `dvc repro` defines input preparation and frozen inference; use `dvc commit` to adopt already generated outputs.

## Scope

Generic 3m-wide conical crowns 4/6/8/10m tall above2m, represented by1600 weighted particles. Fixed +X wind, artificial1500°C source for20s, no trunks, buildings or embers. Independent setup-to-snapshot classifiers have no evolving material/fuel state, recurrence or guaranteed temporal consistency. This is not real-world physical validation.

## Validation

All4,720 exported snapshots passed sparse-mask and recomputed confusion-count checks. On400 shared cases per model, CPU/GPU confusion-count entries differed by at most6 cells (49,152 cells per snapshot). Cold-model counts matched exactly. This count comparison does not prove identical spatial masks. Viewer metrics are computed from the displayed CPU masks; original learning curves retain original GPU metrics.

Browser checks verified actual rendered truth/prediction masks, synchronized rotation, parameter selection and180s undefined positive-class metrics. Narrow windows stack the views; widen the window for side-by-side comparison.
