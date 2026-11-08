# Raw-data migration and proposed training data

This work preserves raw simulation data and logs before removing local copies.
It does not launch new simulations or model training. Existing completed cases
remain accepted only under their original verification records; incomplete runs
are retained as incomplete and are not silently added to training sequences.

## Preservation

Existing DVC output records must not be recomputed from partially removed local
folders. Preserve their original hashes. Upload remaining cloud archives as
byte-identical historical inputs using `scripts/dvc_hf.py track` and `push`.
Each archive must pass the public-data policy, remote size/Xet-hash checks and
Git pointer publication before its temporary downloaded copy is removed.
Financial records and credentials remain private. Any rejected archive requires
explicit inspection and a documented export; it must not be described as fully
preserved. Cloud deletions are not part of this migration script.

The migration inventory is pinned to cloud object generations and MD5 hashes.
Archive parts additionally require the source manifest's SHA-256 hashes.
Missing cloud generations are recorded as missing, never as backed up. Existing
local copies and interrupted-run checkpoints must be audited separately before
final removal. An independently restored sample must pass byte/hash checks.

## Proposed target states

Keep the previous definitions: estimated remaining water, estimated remaining
unreacted fuel, fuel gas release rate, surface heating index, cone presence,
pivot height, tilt from vertical, axial length, end radius, and peak temperature
inside the cone. Heating is not energy; gas release is not combustion heat.
The cone is a fitted >50 C hot-gas envelope with 95% recall, not a physical flame
boundary. Preserve fit quality and boundary clipping as audit fields.

A checked current-run temperature volume has six frames at approximately
0, 36, 72, 108, 144 and 180 seconds. The previous abstract-tree dataset had
91 frames about two seconds apart. The current raw data cannot supply equivalent
two-second cone targets. Do not interpolate missing labels and call them truth.
The user explicitly authorized using the six available cone samples and
interpolating between them on November 8. This resolves the conversion blocker.
Use piecewise-linear interpolation at actual source timestamps onto the finer
training timeline. Preserve all original cone samples and an observed/interpolated
mask, bracketing source times and interpolation weights. Do not extrapolate.
Keep the finer four-state histories; do not replace them with six-frame histories.
Retain denser original cone observations wherever available.

Interpolate the six cone channels, including a soft presence indicator. Use the
previous zero-geometry convention at inactive source samples and document its
transition artifacts; interpolated presence is not a measured or calibrated
probability. Keep the original activity mask and validate finite values, original
endpoints, and no interpolation overshoot. Intermediate peak temperatures are
interpolated endpoint values, not observed interval maxima. The animations and
sample records must clearly distinguish observed from interpolated cone values.
These targets cannot recover rapid cone changes between saved frames.

No new paid simulations or model training are authorized. Training-data extraction
follows verified backup and the requested local-copy cleanup, using bounded
restores where required rather than restoring the entire raw dataset.

## Proposed inputs (enumerated before processing)

- Categorical tree type, one-hot encoded: pine-inspired, eucalyptus-inspired,
  oak-inspired. These are generic-fuel geometry families, not calibrated species.
- Total tree height, crown base height and crown width, metres.
- Ignition contact x/y relative to the tree centre, ignition height, metres,
  and categorical base/crown ignition mode. The contact coordinates encode
  horizontal direction and offset without a redundant integer angle index.
- Wind speed, moisture fraction and loading multiplier.
- Initial water and unreacted fuel masses using the previous definitions,
  after checking how the new vegetation and woody particle classes map to them.
- Time-varying ignition-on fraction and actual timestep duration.

Mesh spacing, domain dimensions, original deck hashes, actual saved timestamps,
run provenance and completeness masks are retained as metadata, not proposed
model inputs. Retain original environment-group train/validation/test splits;
historical pilot cases have already been inspected, so these are not pristine
unseen tests. Any additional geometry descriptor requires enumeration before use.

The simulations use a 0.5 m mesh, an imposed 0.4 m / 1500 C ignition patch for
20 seconds, and a 180-second target. They omit bark, embers, grass and a resolved
solid trunk. Domain sizes vary with tree geometry. Preserve those limitations
in the training-data manifest and do not claim equivalence to real-species fire.

## Scope and requested deliverables (November 8)

The archive, DVC/Hugging Face verification and subsequent local-copy removal
scope covers ALL simulation experiments, not just Experiment 51. Temporary
cloud holds do not satisfy preservation: bytes must be downloaded, DVC tracked,
uploaded with the repository script and remotely verified.

After compatible training data is ready, produce two representative animations
rendered directly from that training data, not predictions. Record case selection,
actual saved timestamps, units, fixed geometry, and cone interpretation. Verify
rendered states against the exact dataset rows; do not present interpolated frames
as additional simulation observations.

Also deliver one readable and machine-readable sample consisting of initial fixed
conditions, the first state, and the next state, with names, units, timestamps and
provenance. Include all ten target values and mark interpolated cone values explicitly.
The sample must not silently include a history window or unavailable cone labels.

A 15-minute monitor tracks transfer, verification, cleanup, training-data conversion,
the two animations and the single-transition example as separate stages.
