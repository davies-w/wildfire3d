# Resolution and profiling study

18 completed/attempted recorded local runs. All use four OpenMP threads; no early ignition stopping.

Fine-grid differences measure sensitivity, not validated real-fire error. The 8-second flow/fire windows are transient mechanism screens, not statistically converged LES averages. Local refinement retains fine cells in x=2..6 m and coarsens upstream/downstream only; the finest cells still constrain the global timestep.

| Case | Cells | Steps | Wall s | Max surface-temperature difference vs fine (C) | Wake velocity RMSE (m/s) |
|---|---:|---:|---:|---:|---:|
| flow_coarse | 1024 | 109 | 2.73 | 0.000 | 0.985 |
| flow_fine | 65536 | 520 | 51.45 | 0.000 | 0.000 |
| flow_local_fine | 36864 | 530 | 50.44 | 0.000 | 0.741 |
| flow_medium | 8192 | 240 | 7.16 | 0.000 | 0.898 |
| flow_radiation | 8192 | 240 | 5.37 | 0.000 | 0.898 |
| flow_split_fine | 65536 | 532 | 73.47 | 0.000 | 0.565 |
| fire_coarse | 1024 | 112 | 3.09 | 97.953 | 1.281 |
| fire_fine | 65536 | 786 | 107.85 | 0.000 | 0.000 |
| fire_local_fine | 36864 | 764 | 90.82 | 95.829 | 0.619 |
| fire_medium | 8192 | 314 | 10.70 | 192.156 | 0.907 |
| fire_radiation | 8192 | 316 | 8.93 | 175.712 | 0.937 |
| fire_split_fine | 65536 | 784 | 141.13 | 65.303 | 0.981 |

## Analytical/conservation checks

{
  "slab_conduction": {
    "time_window_s": [
      100,
      2000
    ],
    "max_abs_error_C": 0.8206537257112245,
    "description": "Analytical insulated slab convection solution, Bi=100, alpha=1e-6 m2/s; temperatures from DEVC"
  },
  "pine_mass_conservation": {
    "initial_mass_kg": 1,
    "max_abs_error_kg": 0.0005395200000000155,
    "final": {
      "Time": 10.0,
      "fuel gas mass": 0.64049311,
      "water vapor mass": 0.2000464,
      "solid mass": 0.16
    },
    "description": "Closed hot box, solid plus evolved fuel and water mass; pyrolysis, not gas-phase flame validation"
  }
}

## Timing repeatability

{
  "flow": {
    "wall_seconds": [
      7.155637165997177,
      6.499852832988836,
      6.448329124948941
    ],
    "max_over_min": 1.1096885762718938
  },
  "fire": {
    "wall_seconds": [
      10.698697832995094,
      10.085284916916862,
      10.106038124999031
    ],
    "max_over_min": 1.060822566851761
  }
}

Boundary-file evidence is recorded separately in results/boundary_check.json. No property ignition probability or material validation is claimed.
