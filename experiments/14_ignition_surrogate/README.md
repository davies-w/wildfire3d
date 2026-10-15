# 14 — Property ignition surrogate feasibility

Target: any part of the designated main structure reaches its material-specific ignition condition within a stated exposure period. The first implementation uses the same 350 °C prescribed-ignition condition as its synthetic FDS wall; this is not a universal material threshold.

This experiment contains an executed acquisition/geometry pilot and a small acceleration screening suite. It does **not** yet contain validated wildfire simulations of the acquired properties, calibrated ignition probabilities, or a trained DNN.

## What is reproducible here

- Twelve real candidate building footprints in three Sonoma regions, each with a 120 × 120 m surrounding area, sampled at 1 m from 2022 DEM, DSM and canopy-height services. County records identify eleven as Single Family Residence and one as Multiple Family Residence; this is not a field inspection. These are rectangular context windows, not surveyed property boundaries.
- Original GIS metadata and exports under `data/sonoma/`; reconstructed observation meshes, arrays and scene metadata under `data/scenes/`.
- Twenty-four coupon runs: six imposed heat fluxes and four configurations. These verify labels and stopping behavior, not wildfire physics.
- Thirty-two coupled burner/structure runs: two burner strengths × two separations × two wind speeds × four configurations. These screen flame/radiation transport at a 30 s horizon; they contain no vegetation or embers.
- One additional coupled reference repeat checks run-to-run differences. One repeat cannot characterize the full variance.
- `results/comparison.json`: measured cost/error comparison, including false and missed ignitions and ignition-time error. All timing results are single measurements; no confidence intervals or cloud-cost claims.
- `results/existing_profiles.json`: actual routine timing from experiment 13, with paths to the source data.
- `scenario_manifest.json`: 240 prospective property/wind combinations, explicitly not runnable until geometry, fuel, material and exposure review. They are coverage samples, not a weather probability distribution.

## Data quality findings

The DEM and canopy image-service descriptions explicitly say that pixel values were converted to **feet**, while generic ArcGIS item text says metres. The DSM remains in metres. Horizontal reprojection does not convert elevations. `pilot.py` applies and records explicit vertical conversions and rejects a changed service description. The international-foot versus survey-foot distinction is below this source's useful precision and remains documented.

Tree crowns overlap some building footprints. Observed height over a footprint is therefore not automatically roof height. The scene files retain canopy-overlap fractions and a separately labeled, unvalidated roof-height estimate. They never silently invent species, siding, roof materials, fuel load, moisture, fences, decks, eaves or vent details. Connected canopy regions may contain multiple plants. Resampling these 1 m inputs onto a 0.25 m solver grid cannot recover missing fences or eaves.

`observed_surface.obj` is a 2.5D observed surface, not a watertight CFD solid. It cannot resolve canopy undersides or roof overhangs. Every scene has `eligible_for_training=false`. The plot in `results/geometry_qa.png` is geometry QA only.

## Ignition-label integrity

The authoritative positive label is the `ignition_wall` activation in FDS's `*_devc_ctrl_log.csv`. A coupled test demonstrated why: the KILL control can stop FDS **after** the last periodic temperature CSV record, leaving that final sample below the threshold. Using only that sample mislabels an actual ignition as negative.

`benchmark.py` reads the activation log and requires successful solver completion. A completed full-horizon run without ignition is negative; a crash, timeout, malformed result or prematurely truncated negative is not a training label. Seven regression tests cover these cases. `check_boundary.py` independently uses fds2ascii to verify the coupon's west-wall boundary temperature; its measured value and time window are in `results/boundary_check.json`.

The maximum-temperature DEVC filters by the main wall's unique SURF_ID and scans all its exposed boundary cells, not a single probe point. A future property deck must use unique surface IDs and thresholds for **all** main-structure components, OR their activation conditions, and exclude sheds, fences and vegetation from the building label.

## Baseline limitations

Experiment 13 remains a useful regression fixture, but is not an accepted material model for production labels. In particular its GLASS surface is combustible WOOD with a 180 °C threshold, its roof is WOOD with a 550 °C threshold, and vegetation is represented by impermeable burning blocks. Its old visualization checks focus on wall/roof and cannot establish the user's new “any component” target. Those decks were not changed here.

The previously reproduced FDS 6.11.1 mixed GEOM/OBST particle crash has not been repaired or qualified by this experiment. Observed-property meshes must not be declared production-ready merely because the synthetic OBST screening suite runs.

## Reproduction

From the repository root, use the native arm64 FDS and four OpenMP threads, as required by AGENTS.md:

```sh
.venv/bin/python -m pip install -r experiments/14_ignition_surrogate/requirements.txt
.venv/bin/dvc repro experiments/14_ignition_surrogate/dvc.yaml
```

The acquisition stage requires internet access; MPI requires local socket access. `paths.py` resolves the engine. Binary and deck hashes are stored per run. The DVC benchmark dependency pins the default native binary path; if WILDFIRE3D_FDS is overridden, update that dependency too. Solver outputs belong in DVC, never Git. No renderer is required.

Existing completed simulations are reused only when their deck and binary hashes match, then labels are re-read with the current parser. Delete only the desired case's `result.json` to deliberately remeasure runtime. A stage cache hit is not a fresh timing measurement.

## Sources and attribution

- [Sonoma public data portal](https://sonomavegmap.org/) and its [acknowledgment](https://sonomavegmap.org/docs/acknowledgement.txt). The old acknowledgment covers 2013 products; the 2022 portal item/service metadata is retained separately and must not be confused with that older grant.
- [County building outlines](https://socogis.sonomacounty.ca.gov/map/rest/services/BASEPublic/Buildings/FeatureServer/0): original vintages vary, coverage is incomplete, and some historic outlines are point placeholders. Selection excludes very small outlines. Full service metadata is retained; redistribution/training terms require confirmation where no explicit license is supplied.
- 2022 LiDAR funders listed by the publisher: California Natural Resources Agency, State Coastal Conservancy, NASA, USGS, Sonoma Water, UC San Diego, Sonoma Ag + Open Space and Humboldt Bay Municipal Water District. Coordinators: North Coast Resource Partnership and Solano County. Technical team: NV5 Geospatial and Tukman Geospatial.
- [FDS manuals](https://pages.nist.gov/fds/manuals.html); local 6.11.1 manual/source checked for DEVC surface statistics, KILL controls, radiation options and CPU timing.

No Google Maps content was acquired or used.

## Remaining before property-scale training

1. Verify residential use, building/imagery dates, footprint registration, occluded roof geometry and data-use permissions.
2. Annotate or probabilistically specify materials, assemblies, vegetation fuels, fences, decks and ignition exposure; keep observed and assumed values distinct.
3. Qualify the engine's GEOM/particle fix or a tested geometry representation; validate the selected material and vegetation mechanisms against relevant experiments.
4. Run full-horizon paired property scenarios and replicated stochastic seeds. Set error tolerances on missed ignitions, false ignitions and time, including confidence bounds.
5. Only then scale the manifest, introduce active selection of expensive runs, and train a baseline surrogate with entire properties/geographic areas held out.

The screening results do not establish a five-percentage-point error bound. Eight transport scenarios cannot establish that bound, even with zero observed classification errors. Keep conditional vulnerability separate from annual risk and assign scenario probabilities only from a justified joint exposure/weather model.
