# Coast-live-oak-inspired addition

Adds type2 (coast live oak) alongside existing type1 pine and type3 eucalyptus. One tree per case. This is the existing experiment47 proposed oak shape, not a measured species-average specimen: nominal10m height,12m crown width,3m crown base, overlapping ellipsoid crown and forked woody stems. Crown overlap forms a union and does not duplicate fuel.

The design follows the same25 size combinations (height8–12m; x crown radius4–8m) and40 balanced cases per geometry:20 trunk-base and20 crown-contact heating locations, eight compass directions, wind1–5m/s, moisture0.06–0.30 and loading multipliers0.7/1/1.3. This creates1,000 candidate cases, not1,000 launched simulations. Five size combinations provide10 pilot candidates (both ignition families) and no extra-height control, per user decision.

Use29×20m X/Y,0.5m gas cells, and Z=max(16m, tree height+6m). No extra-height experiment is included. The user's acceptance of compact-domain differences is retained: prior experiment49 flagged7/22 old/new comparisons, so compact boundaries are an accepted approximation, not validated equivalent boundaries. The29×20m footprint gives each oak size variant at least the per-wall clearance of both corresponding pine/eucalyptus radius-offset variants in their24×16m domains. This is a geometric clearance match, not a proof of boundary adequacy.

Retain generic vegetation/wood chemistry, weighted crown particles, static thermal woody particles, and imposed0.4×0.4m1500°C heating for20s. No species-calibrated live-oak combustion, protective bark, embers, grass or resolved solid trunk obstruction.180s physical horizon, four threads when run; no local FDS/training.3D temperature snapshots explicitly36s, matching the previous actual cadence;2D slice cadence2s. No dense-temperature-history claim.

Status: offline design/input preparation only. No cloud job, budget reservation or training started. Actual cloud parser, first-positive mass and portable restart checks must pass before any full solve. Future pilot uses bounded stop/checkpoint/resume policy and budget accounting before launch. Existing48/49 decks and results remain unchanged.

The combined planned dataset is3,000 unique cases:1,000 pine,1,000 eucalyptus and1,000 coast-live-oak-inspired. Pilot subsets are not additional design cases. This is a planned count, not a claim that3,000 simulations have run.

User approved the same variations and a small10-case cloud pilot, with no additional height experiment. The combined simulation-and-training ceiling is tracked privately. Pilot measurements must inform the3,000-case campaign plan and leave room for training rather than assuming every planned run is already funded.
