# Fresh four-state prediction on species-inspired scenarios

This experiment predicts remaining water (kg), estimated unreacted fuel (kg), fuel-gas release (kg/s), and surface-heating index (K). It has no cone inputs, targets, or loss. All 1,899 verified scenarios are included, including 19 whose cone fits failed. There are 91 four-state samples over 180 seconds; these are distinct from the six saved spatial temperature fields used for cone fitting.

The user approved ten approximately balanced environment-group folds and one fixed rotation: folds 0–7 train (1,522 cases), fold 8 validation (152), fold 9 test (225). Every wind–moisture combination stays in one fold, as does every physical configuration. Fold allocation uses only counts, seed 3516, and two or three environments per fold; it never uses response values. Previously viewed scenario previews mean this is not a pristine unseen collection. Test metrics remain unopened until validation selection is frozen.

The fresh model has eight prior four-state samples, GRU64, shared dense64/SiLU, four delta outputs and three internal soft gates (26,695 parameters). Neither weights nor optimizer are continued from an earlier experiment. Missing initial history repeats the initial state. The recurrent training prefix uses observed past states without gradient; the predicted future within each window carries gradients. Evaluation rolls autonomously from the initial state. No positivity, monotonicity or physical cessation constraint is added.

Static inputs are pine/oak/eucalyptus family indicators; height, crown base and width; three relative ignition coordinates; base/crown ignition mode; wind; dry-basis moisture; loading multiplier; initial water and fuel mass. Interval-average imposed ignition strength and elapsed time are dynamic inputs. This gives 17 external values plus 32 history values. Continuous static normalization and the established asinh state normalization use training configurations only; categorical indicators are unchanged.

The objective is the actual-time integral of absolute piecewise-linear physical error, divided by each reference history's range and duration, then averaged over the four states. Gate BCE weight is 0.1. Configuration weighting, AdamW learning rate 0.0003, weight decay 0.0001, gradient clipping 1 and batches of 256 windows follow the earlier model. Curriculum horizons are 1/8/16/32/64/90 steps from epochs 1/21/41/61/110/130. Nominal minimum 160, maximum 400, validation patience 30 after the final curriculum transition. A private allocation guard can stop earlier to protect final evaluation. Validation full-rollout integral selects the checkpoint. The test fold is evaluated only after selection freeze.

The original simulations use species-inspired geometry and generic fuel, not calibrated species. They use a 0.5 m mesh, a 0.4 m contact patch imposed at 1,500 °C for 20 seconds with 0.1-second ramps, and 60 kW/m² source HRRPUA on contact particles. No embers, bark, grass or resolved solid trunk are included; woody stems are thermal particles. The heating index is not energy. Unreacted fuel does not measure all remaining solid mass or char. Temporal resampling cannot recover unsaved fluctuations. These limitations bound what successful state prediction establishes.

`prepare_data.py` verifies source hashes, physical initial-mass receipts, exact agreement between available cone variants and original four-state histories, monotonic timestamps, finite values and nonzero target ranges. `prepare_split.py` checks separation. `check_local.py` runs forward-only checks and tests normalization isolation. `cloud_check.py` measures actual losses and exercises nonempty optimizer next-update restoration on disposable probe weights. Those probe weights are discarded before fresh training. Cloud epoch checkpoints include optimizer and random states. Interrupted work must resume from a verified completed-epoch checkpoint; no automatic paid retry is configured.

Financial and operational records live under ignored `private/`; they are never artifact-upload inputs. Scientific datasets and final model outputs are preserved with the repository DVC/Hugging Face workflow. Source observations remain traceable in the schema; recreating them requires their original restoration locations.

## Completed result

The run completed 196 epochs, stopped by validation patience after the full 90-step curriculum, and selected epoch 166 using validation alone. Validation integral error was 18.43%; the 225-scenario test integral was 42.18% in the cloud report and 42.17% when independently decoded on CPU. The exact physical constant-initial-state baseline is 45.11%, giving about 6.5% relative improvement overall.

| State | Model integral error | Exact constant-state baseline | Model physical MAE |
|---|---:|---:|---:|
| Water | 10.09% | 57.74% | 3.34 kg |
| Unreacted fuel | 138.50% | 79.58% | 20.40 kg |
| Fuel-gas release | 7.46% | 17.37% | 0.196 kg/s |
| Heating index | 12.62% | 25.77% | 5.68 K |

These percentages divide errors by each reference history's own variation, not its initial mass; near-constant fuel histories can therefore receive very large normalized errors. Fuel generalization is weak despite improvements in the other three states. This is a mixed result from one grouped rotation, not robust species validation. The unconstrained model also predicts negative heating index in 50.3% of evaluated forecast samples and negative gas release in 0.29%; these are prediction defects, not physical measurements.

Numerical audit: the cloud control round-trips initial states through normalized float32 encoding, yielding a 45.50% baseline. Holding the physical initial states exactly constant corrects that to 45.11%; use the corrected figure for comparison. Independent CPU decoding differs from CUDA by 0.0724 percentage points in the fuel metric (0.0181 points overall). This is disclosed in `final-verification.json`; the arithmetic check is not bitwise equivalence. Original cloud reports and predictions remain unchanged. No parameters were tuned after viewing the test.

All 415 scientific result files, including the selected model and resumable epoch checkpoints, were independently restored from Hugging Face. Source and artifact metadata are Git-published. The completed cloud job, its VM and its disk were removed; its temporary read grant was revoked. Financial closeout remains private and posted billing may lag usage.
