# Two-case training-data preview

This is a review sample, not bulk conversion and not model training. All original
local raw simulation data is retained. Bulk conversion and raw-data deletion wait
for the user's review. Training data remains local even after verified HF upload.

The selected train-split cases are `tree51_001323_baseline` (26 m eucalyptus-inspired
geometry, 15 m crown width, crown ignition at 13.4 m) and
`tree51_001336_baseline` (10 m oak-inspired geometry, 12 m crown width, base ignition
at 1.25 m). They are examples selected from already-backed-up cases, not a random
or representative performance evaluation. They use generic vegetation material,
not calibrated eucalyptus or oak fuel behavior.

Each output directory in `data/training-preview` contains:

- `training.npz`: 91 actual particle timestamps, ten states, original six cone rows,
  observed/interpolated masks, bracketing indices and weights, timestep and ignition
  schedule values, and initial particle coordinates used only as geometry context.
- `training.csv`: all ten states with units, timestamps and cone provenance.
- `metadata.json`: fixed model inputs, geometry context, original archive/member
  hashes, class masses and fitted cone coverage/precision/boundary diagnostics.
- `first-transition.json` and `.md`: fixed initial conditions, initial state and
  the next state. No historical state window; no predictions.
- `training-animation.gif`: every dataset row, in order, at 6 display frames/s.
  Display playback speed is not physical simulation time; the title gives the
  actual simulation time. Gray chart traces show the dataset trajectory for
  context, not inputs given to a model. Blue dots show the exact displayed row.
- `animation-verification.json`: dataset hash, rendered row indices/timestamps and
  state hash. `validation.json` at the output root checks both examples.

## State interpretation

Water and unreacted fuel are estimates using the prior four-state definitions:
water-vapor mass-loss integration and fuel-vapor integration divided by 0.75.
The latter estimates remaining unreacted vegetation, not all remaining solid
material. The raw simulation includes char oxidation. Fuel-gas release is kg/s,
not heat release. Heating is the mass-weighted particle surface-temperature
excess above 20 C divided by initial wet mass, in K; it is not energy.

All seven vegetation/roundwood/stem particle classes contribute. The imposed
contact ignitor is excluded. Initial class masses are checked against the original
deck design. CSV-integrated channels are evaluated at actual particle timestamps.

The cone is a deterministic fit to cells above 50 C, with at least 95% hot-cell
coverage at the six saved volume timestamps. It is not a physical flame boundary.
Its apex is constrained to the tree axis and its tilt to the downwind x-z plane.
The fitted cone can include substantial cool air. Hot gas reaches the domain
boundaries in the eucalyptus example: the fit sees only the simulated domain, and plotted
cones are clipped to that domain. Fit precision and hot boundary-cell counts are
provided for every observed source frame. The oak example has no >50 C cells in
its six saved volumes. This does not establish absence of short-lived hot gas
during the 20-second ignition or between saved volumes; interpolation cannot
recover such events.

Intermediate cone rows are **piecewise-linear interpolations**, not extra measured
simulation frames. Presence is a synthetic fractional indicator, not a calibrated
probability. Inactive source rows have zero cone geometry and a zero temperature
sentinel, not an ambient-temperature measurement. Interpolating from/to these zeros
can yield a slowly appearing/shrinking cone and synthetic temperature ramps. It
cannot recover fast plume changes or unobserved peaks. Original endpoints remain
available and no extrapolation is used.

Fixed outlines show initial geometry, not burn state; orange shows the fitted
hot-gas envelope with opacity scaled by synthetic presence, not a raw temperature
field. Red stars mark the imposed contact ignition while its ramp is active.

The 0.5 m grid uses a 0.4 m contact patch with 1500 C imposed temperature, 20 s
source duration and 0.1 s ramps; the contact particles also impose HRRPUA=60 kW/m2.
Bark, embers, grass and a resolved solid trunk are absent. Stems are cylindrical
thermal particles. Domain sizes are 24×16×32 m and 29×20×16 m respectively.

## Reproduction and preservation

`training-preview-sources.json` pins the two raw archive pointers and SHA-256 hashes.
Both were independently restored from HF before conversion; every extraction input
was compared to its archived member and accepted completion proof. If the original
archive is evicted, the extractor also accepts its bounded restore under
`.artifact-staging/two-case-preview-restored/` using the same repository-relative
path. Restore those two pointers with `scripts/dvc_hf.py restore` before extraction.
Existing local `completed07` inputs must be available and match their original
proofs. No solver execution is involved.

The frozen `training_preview_two_cases` DVC stage records these outputs. The source
and metadata are Git-published; output objects are uploaded with the scoped
`scripts/dvc_hf.py` mechanism using a separate private plan so the ongoing raw
archive migration's plan is not overwritten. Read preservation receipts for actual
upload and restoration success; this description alone is not an upload receipt.
