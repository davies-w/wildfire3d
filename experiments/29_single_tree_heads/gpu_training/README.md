# Full-resolution cloud continuation

User requested laptop training stopped and transferred to Google Cloud. Completed previous, scalar-strength and bounded models retained. Paused heads process had no checkpoint; its 1600-step progress scores are preserved but its weights were only in memory, so the heads fit restarts from the same saved warm start for 3200 steps. No scientific target or split changes. All 32 training and six development-validation cases, all 91 frames and full 48x32x32 six-channel arrays are transferred. No test cases or new FDS simulations. Same generic crown, artificial 20-second ignition and omitted embers/buildings as parent experiment. CUDA replaces MPS, so results need not be bit-identical. Regular optimizer/RNG/model checkpoints are uploaded, with a next-step reload check. No automatic Spot retry. One L4 Spot VM; $1 run cap, 20-minute queue, 45-minute VM age and 65-minute absolute deadline. Expected $0.15–$0.40; cap is enforced through runtime limits rather than a billing hard limit.

Attempt 01 failed before data download/training because Batch escaped a multiline command; job-status.json preserves the failure. Cleanup was verified before attempt 02. The corrected workflow uses an encoded single-line bootstrap, as in the successful hardware benchmark. Overall reservation remains $1, with $0.20 conservative allowance for the failed attempt and $0.80 for attempt 02. Attempt 02 has 20-minute queue, 30-minute VM/task and 50-minute absolute deadlines. Runtime limits include setup; no automatic retry.

## Completed results

Full heads fit completed in 74.74 seconds, excluding initial validation and cloud setup. Selected step 3200. All six variants evaluated over full histories. All VMs, disks and Batch jobs deleted; temporary single-object read access removed. Checkpoint optimizer/RNG reload passed in-process, but actual Spot replacement was not tested.

| Variant | Hot temperature MAE (C) | Heat-release relative L1 | Radiation-dose relative L1 | Flame IoU |
|---|---:|---:|---:|---:|
| previous | 46.00 | 0.3310 | 0.3492 | 0.5186 |
| bound_only | 46.00 | 0.3310 | 0.3492 | 0.5186 |
| bounded | 44.45 | 0.3440 | 0.3174 | 0.5176 |
| strength_only | 46.00 | 0.3080 | 0.3492 | 0.4981 |
| heads | 44.60 | 0.3080 | 0.3130 | 0.5422 |
| interpolation | 55.51 | 0.4734 | 0.4089 | 0.4726 |

These are development-validation means over 22–180s, not independent test accuracy. The six validation cases selected checkpoints and have been reused in development. Improvements are modest. The 6C floor removes extreme negative predictions by construction; scalar normalization alone accounts for the change in total heat-release error. Separate branches improve spatial combustion overlap and radiation while temperature is slightly worse than the bounded-only fit. Same generic crown and artificial ignition; no claims of real-world validation or sequence learning. Estimated total run cost $0.15–$0.40, not an invoice; full $1 reservation retained.

Material tradeoff: validation post-source peak-temperature error worsened from 66.6C (previous) to 210.8C (separate heads), despite lower average hot-region, heat-release and radiation errors. The model is not an across-the-board improvement and should not be accepted solely on the combined score.
