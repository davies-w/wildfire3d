# Stage 3: controlled tree-height and fuel-loading pilot

Twelve new FDS configurations: crown heights6/8/10m above a2m base, diameter3m fixed, loading multipliers0.8/1.2, forcing profiles1.8m/s at240degree ignition and3.8m/s at300degree ignition. Generic cone material classes, moisture0.12, 20s artificial hot-particle arc, 0.5m cells,24x16x16m domain and180s horizon; no trunks/buildings/embers. Nonflammable ground unchanged. Taller crowns leave less vertical air clearance; this pilot does not re-establish domain/grid convergence. Fuel loading scales represented particle weights; height scales z and total mass to preserve density before the loading multiplier. Exactly1600 vegetation particles retained, no resampling.

Eight training/two validation/two untouched-test configurations, defined before simulation. The same factor values occur in training and test, with complete combinations withheld. This tiny factorial is not broad i.i.d. coverage of arbitrary trees, species or shapes. It tests sensitivity to two geometry/material factors within a narrow range. Old fixed-tree training cases may be reused, with configuration-balanced sampling. Test simulations cannot launch until frozen trained weights and autonomous predictions exist. Both test outputs will remain unseen until that freeze.

Native0.1s input checks passed on three training extremes: all400 particles per class match expected coordinates and weight factors. Same-Linux checkpoint resume is checked before each full cloud solve. Raw particle/slice/boundary/restart evidence retained. No paid launches until sequence-stage result/decision recorded. Six two-case CPU groups reserve$0.20 each, $1.20 total; follow-up GPU allowance up to$1. Remaining$0.30 reserved margin within$2.50 stage cap. No automatic retries or recycled reservations. Typical original cases took320–456s on4vCPU; height/loading variants may differ. Expected extra actual cost roughly$0.50–$1.00, not a billing guarantee.

## Learning comparison after sequence failure

The standalone recurrent model in experiment30 failed: full-rollout objective2.30 versus0.073 for snapshot prediction, despite teacher-forced one-step0.065. This stage compares a geometry-conditioned snapshot model against a hybrid that adds a bounded +/-0.5 encoded-unit recurrent correction to the frozen snapshot prediction. The hybrid receives the snapshot at the requested time, so it is not a standalone physics propagator. Its history is only justified if it improves on the same snapshot prior and the state-reset diagnostic. The snapshot conditions on four mass-distribution summaries (total represented mass, vertical mean/variance and foliage fraction), adequate to describe this narrow height/loading variation, not arbitrary branches/shapes. The recurrent branch receives the full four-channel initial density map, decoded gas fields and predicted material state. It is trained on160 full autonomous90-step trajectories with gradient truncation every8steps; no teacher states are reinserted. Snapshot receives3200 batch-two updates. Training exposures and compute are unequal and will be reported. Half of updates sample old geometry and half new geometry; validation selection weights old/new groups equally. Fresh tests remain untouched until both models and predictions are hashed.

All ten development simulations reached180s, with wall times274.5–412.1s on4vCPU. Initial particle-density descriptors match raw FDS data within floating-point error (maximum per-case discrepancy recorded in results/learning-data-audit.json). The GPU input contains48 development configurations:32 original training +6 original validation +8 new training +2 new validation. Fresh tests v31_04 and v31_11 are absent from simulation outputs at submission. Their initial geometry descriptors are known inputs. The recurrent source flag is sampled at the start of each2s transition, approximating the20.1s source cutoff; it is conditioning information, not imposed heat. Checkpoints retain optimizer and RNG states and support explicit restoration via RESUME_CHECKPOINT; no automatic paid retry.

The geometry snapshot starts from the earlier `previous.pt` snapshot weights, then adds four geometry descriptors and a6°C temperature floor; it is not the separate-output-heads/strength model from experiment29. The hybrid starts from experiment30 recurrent weights with its field correction head zeroed, then trains the bounded correction. These are explicit architectural choices, not evidence that this is the best possible sequence architecture. Each FDS configuration has one realization; variability across repeated turbulence/particle realizations is not estimated.


## Completed result

The standalone recurrent model in experiment30 failed autonomous rollout (combined validation objective2.302 versus snapshot0.0728, about31.6x worse), despite teacher-forced next-step objective0.0654. This is evidence of rollout failure, not successful sequence learning. Stage31 therefore tested a separately disclosed hybrid snapshot-plus-recurrent-correction model.

Fresh predictions and trained models were frozen before the two test FDS jobs were submitted. All frozen hashes were rechecked before evaluation. No FDS state is fed into prediction. Both test cases completed180s.

| Fresh case | Model | Hot-region MAE °C | HRR curve relative L1 | Radiation-dose relative L1 | Peak error °C |
|---|---|---:|---:|---:|---:|
| v31_04 | snapshot | 57.1 | 0.569 | 0.328 | 154.2 |
| v31_04 | hybrid | 55.5 | 0.551 | 0.340 | 93.9 |
| v31_04 | state_reset_ablation | 54.8 | 0.777 | 0.346 | 146.8 |
| v31_11 | snapshot | 52.3 | 0.819 | 0.518 | 502.1 |
| v31_11 | hybrid | 52.0 | 0.826 | 0.515 | 490.1 |
| v31_11 | state_reset_ablation | 51.7 | 0.826 | 0.510 | 332.1 |

FDS output timestamps are slightly irregular: reference fields were linearly interpolated onto the frozen2s prediction times, with maximum nearest-frame offsets0.175s and0.074s. Predictions were unchanged, and no extrapolation was used. Metrics above cover source-off times>=22s. Hot-region error uses cells where either truth or prediction exceeds50°C. Radiation is integrated gas radiation intensity, not incident wall heat flux. Full-volume heat-release history and spatial radiation-dose errors are dimensionless;1.0 means100% relative L1 error. The report also contains airflow and flame-region overlap (HRRPUV>10kW/m³), not a visual flame label.

Snapshot training took42.3s and hybrid training170.3s on an L4. Median inference for91 frames/180s was0.072s snapshot and0.216s hybrid on that GPU, excluding output transfer/rendering; this is not laptop CPU timing.

The hybrid uses the snapshot prediction at each requested time and a bounded learned correction. It is not a standalone physics solver. Its2m internal state predicts0.5m output fields. State-reset ablation removes persistent predicted state and latent memory; it is an ablation of the trained hybrid, not an independently retrained architecture. Snapshot and hybrid training budgets differ.

Only two fresh configurations, one generic cone family, crown heights6/8/10m, diameter3m, fixed0.12moisture, two forcing profiles, loading0.8/1.2. Frozen particle geometry;0.5mFDS cells;20s artificial1500°C source; no trunks, buildings, combustible ground or embers. Taller crowns reduce top-boundary clearance. Agreement is against this fixed FDS setup, not physical validation.

Stage31 reserved$2.20 of its$2.50 cap; combined with Stage30's$1 reservation the total is$3.20 under the$3.50 ceiling. Reservations are conservative limits, not invoice spend. GPU and CPU cleanup is verified separately in the retained job reports.

Animations: results/v31_04-comparison.gif and results/v31_11-comparison.gif. They show maximum-through-y projected gas temperature and heat-release density with fixed shared nonlinear scales; peaks may be clipped. They are field visualizations, not Smokeview flame/smoke rendering. Histories: results/fresh-histories.png.

### Decision

All three stages are complete. The standalone sequence model failed long rollouts. The bounded hybrid improved the combined development selection objective by15%, but on the two fresh cases mean post-source heat-release error moved only0.694 to0.689 and radiation error slightly worsened0.423 to0.428. It does not establish a useful accuracy advantage over the simpler snapshot CNN. In v31_11, FDS has a strong delayed post-source burn that both learned models miss.

A known training failure must be addressed first: v31_09 has mean post-source FDS heat release0.954kW versus hybrid241.495kW (and peak temperature150°C versus984°C). Its enormous relative error reflects both a small denominator and substantial absolute false heat. The present model does not reliably fit all its training configurations, so buying more simulations is not yet the demonstrated remedy. Next: make the model fit the weak-burn/strong-burn development histories and distinguish fire strength from field placement, then repeat a newly frozen evaluation. No further cloud jobs were launched.

Both test cases were simulated after predictions were frozen;16 frozen files were verified. Final CPU/GPU job, VM and disk cleanup is verified. The conservative compute-only controller-lifetime proxy is$0.411 for both experiments, excluding storage/network/ancillary charges and not an invoice total. Full reservations remain$3.20 against the$3.50 ceiling.
