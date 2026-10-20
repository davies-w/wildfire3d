# Experiment 28: repair single-tree CNN physical predictions

Aim: correct diffuse residual combustion and weak peak/radiation predictions using experiment 27's immutable 32 training and six validation configurations. The old six test cases are now diagnostic evidence, not a fresh test set. No old test fields enter fitting or selection. Original artifacts remain unchanged.

First run a four-training-case reconstruction test, then fit all 32 configurations with validation-only selection. Keep the original transformed field loss, adding per-frame log total heat-release error, physical HRR spatial error, peak-temperature error and radiation spatial error. These are learning objectives, not a guarantee of conservation or physical validation. The initial candidate retains the original CNN architecture and warm-starts the original training-only checkpoint.

Fresh cloud tests are conditional on a substantial reduction in late residual heat release, improved radiation/peak predictions and no material hot-temperature regression on validation. Freeze predictions before any fresh test solve. Reserve any new paid work in experiment 27's central $5 ledger; $0.88 remains unreserved at setup. No cloud work launched at setup.

Unchanged physical simplifications: one generic conical vegetation crown, 3 m diameter and 8 m crown height starting 2 m above ground, 1600 frozen vegetation particles, fixed moisture 0.12 kg/kg dry fuel. Wind +X at 1–5 m/s and ignition azimuth vary. Ignition is 1600 stationary 1500 C particles lasting 20 seconds. Domain 24×16×16 m, uniform 0.5 m mesh, 180-second horizon. Bare nonflammable heatable ground; no trunk, buildings, ground fuel or embers. Radiation output is integrated intensity, not directional incident surface heat flux. Predictions are full 3D fields at requested times, not an autoregressive solver.

## Local repair results before fresh tests

The four-case reconstruction check reduced late (120/150/180 s) mean predicted total HRR from497.6kW to0.0495kW, versus0.00565kW FDS. Peak-temperature snapshot error fell160.5→43.0°C; hot-region snapshot error21.3→22.3°C. These are training reconstruction results, not independent validation.

The full32-case fit selected step2400 of4000 by the six validation configurations. All-timestep post-source validation (22–180s) gave:

| Metric, mean over six validation configurations | Original | Repair |
|---|---:|---:|
| Hot-region temperature MAE |44.59°C|46.00°C|
| Total-HRR time-history relative L1 |103.49%|33.10%|
| Excess integrated-radiation-intensity dose relative L1 |67.79%|34.93%|
| Error in maximum post-source temperature |448.19°C|66.42°C|
| Mean total HRR after120s |516.05kW|0.0000548kW|

The repair removes the enormous diffuse heat background, but now undershoots FDS's tiny late residual. Zero output is not proof of exact extinction physics. The model also retains slightly worse hot-region temperature MAE. Separate physical losses were sufficient for this first candidate; strength/shape factorization has not been implemented or claimed as tested.

Six new conditions are declared with Sobol seed2804. Original CNN, repaired CNN and training-field interpolation predictions were frozen before cloud submission. Every fresh case reserves$0.10 in experiment27's central ledger; six raise the full cumulative reservation from$4.12 to$4.72, within the original$5. No reservations are recycled. Full new-test results remain pending.

## Fresh-test outcome — six untouched conditions

All six FDS runs completed180s. All25 frozen hashes passed revalidation; both original and revised freezes remain intact. The six conditions were not present in any original run. Predictions preceded every submission. Raw fields/checkpoints are retained. No model was changed after opening the new test results.

Mean metrics across six configurations, after source removal (22–180s):

| Metric | Original CNN | Repaired CNN | Training-field interpolation |
|---|---:|---:|---:|
| Hot-region temperature MAE |45.25°C|47.26°C|53.81°C|
| Total-HRR time-history relative L1 |90.23%|34.89%|28.69%|
| Excess radiation-intensity dose relative L1 |53.70%|34.01%|21.51%|
| Maximum-temperature error |409.45°C|90.03°C|122.79°C|
| Combustion-mask IoU (HRRPUV>10kW/m³) |0.516|0.526|0.511|
| Full-domain velocity-vector MAE |0.477m/s|0.497m/s|0.445m/s|

After120s, mean total HRR is507.98kW original,0.00262kW repaired,0.00467kW FDS. The diffuse large background is removed, but per-case tiny residuals remain poorly predicted; relative late errors are unstable near zero. Post-source mean total HRR is980.6kW repaired versus1309.3kW FDS, a roughly25% aggregate underestimate. Thus removing the false tail did not fully recover the main burn's strength.

**Material regression:** temperature is an unconstrained output. Repaired predictions include cold pockets down to−69.25°C; about0.1504% of fresh-test cell/timestep temperatures are below0°C. FDS test minima are above freezing. This worsens a pre-existing original-model defect and also occurs on validation data. No clipping was applied to reported errors. Main temperature animations use20–1400°C and therefore conceal cold undershoot; `results/visuals/cold-artifact.png` exposes it with a separate scale. This is a failed physical-plausibility check, even though several average metrics improved.

Conclusion: physical-unit losses transfer to fresh conditions and substantially improve combustion shutdown, heat history, radiation and peaks. Hot-region temperature and velocity degrade slightly. Interpolation remains stronger on total heat/radiation, while repaired CNN is stronger on hot-region temperature and peak temperature. This is a partial repair, not an FDS-equivalent model, real-world validation, compositional validation, or evidence about other tree shapes/moisture.

Next candidate should constrain/penalize temperature undershoot using development data, and separate total fire-strength prediction from spatial shape to address under-burning. Existing fresh tests are now diagnostic and must not be reused as untouched tests after tuning. No extra paid runs were launched for those future changes.

## Deliverables and cost

- `results/visuals/s28_test_0.gif` and `s28_test_1.gif`:31frames, physical times0,6,…180s; rows FDS/original/repaired. Temperature and HRR are maximum projections acrossY, not visible smoke/flame rendering. Colour scales saturate at1400°C and1000kW/m³; HRR colour floor0.01kW/m³. Right-hand total-HRR traces include all cells without display thresholding.
- `results/visuals/heat-histories.png`: all six cases, original/repaired/interpolation/FDS.
- `results/test-summary.json`, `aggregate.json`, `cold-diagnosis.json`: full numerical evidence including limitations.
- Standalone91-frame inference: median1.09s AppleGPU,1.96s CPU; excludes loading/rendering. No FDS data read during CNN inference. Different hardware from cloud FDS, not a controlled hardware speedup.
- Fresh six-job compute-only proxy$0.07274, using conservative$0.08/VM-hour for controller lifetimes. Excludes storage/egress/logs/workflows; not invoice spend. Fresh conservative reservation$0.60; cumulative original+repair reservation$4.72 of$5, never recycled.
- Final project inventory confirms no VMs, disks or Batch jobs remain.

Independent field/global-HRR comparison shows7–27% active-history discrepancy due to different instantaneous/averaged output cadence and possibly temporal sampling; it is documented, not treated as an exact numerical identity. Learning and reported field comparisons consistently use the same cell-centred instantaneous FDS fields. This does not establish physical calibration of their values.
