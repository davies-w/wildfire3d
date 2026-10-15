# Measured pilot findings

57 synthetic FDS runs: 24 heated-wall checks, 32 coupled flame/radiation runs, and one reference repeat. These are not simulations of the 12 acquired properties.

## Coupled flame/radiation screening

| Configuration | Speedup vs full reference | Extra speedup vs early stopping | Missed / false ignitions | Maximum time difference |
|---|---:|---:|---:|---:|
| coarse | 5.52× | 3.32× | 0 / 0 | 13.073 s |
| early | 1.67× | 1.00× | 0 / 0 | 0.221 s |
| radiation | 1.94× | 1.16× | 0 / 0 | 2.459 s |

Eight scenarios, four of which ignite in the reference; a 30 s exposure horizon. Aggregate speedup is the sum of reference wall times divided by the sum of variant wall times. Single timing samples include startup; no confidence interval is established.

Time differences apply only when both runs ignite; classification differences must be considered separately. Radiation and coarse variants include early stopping. The coarse case changes both spatial and temporal discretization.

Reference repeat ignition-time difference: 0.00000 s. Runtime changed from 33.85 to 87.23 s (2.58×). Other applications were observed consuming substantial CPU at the end of the experiment. The speed ratios above are preliminary, not controlled performance estimates. One repeat cannot quantify all variability.

## Acquired properties

12 registered 120 × 120 m observation meshes and scene arrays, sourced from public Sonoma data. County records: 11 single-family and 1 multifamily residence. DEM/canopy feet-to-metres conversion is explicit. Individual species, materials, fences and eaves remain unverified. These scenes are not yet eligible for training.

## Consequences

- Early stopping is the first practical acceleration candidate; qualify it on full property scenarios before adopting it.
- Coarsening trades substantial ignition-time accuracy for speed. This screen does not establish an acceptable error bound.
- Radiation tuning saves additional work but changes ignition timing; retain a separate acceptance test.
- Existing experiment 13 profiles put radiation at about 21%, output at about 6%, particles at about 0.5%. Particle thinning is not a promising first optimization on those cases.
- The 240-entry property scenario manifest is a preparation artifact, not 240 executed or accepted training labels.

See comparison.json, transport.json, benchmark.json, reference_repeat.json, existing_profiles.json and boundary_check.json for machine-readable measurements; see ../README.md for reproduction and limitations.
