# Ten random existing conifer cases

The user explicitly requested ten random samples from the existing conifer group, using both agreed representations. These are generic-fuel, pine-inspired geometries, NOT calibrated Douglas fir.

Selection: seed2026110901, uniform sampling without replacement among561 unique pine-inspired cases with retained passed180s completion proofs across attempts. The selection is frozen in conifer-cone-selection.json, with no outcome-based filtering or resampling. It is not a sample of all667 planned conifer cases.

Some local raw outputs were evicted before the user's current retain-data instruction. Exact selected files were restored into .artifact-staging/conifer-input-roundtrip using their existing frozen DVC directory manifests, without recomputing partially evicted output hashes. All restored raw inputs were checked against the original completion-proof SHA256 values. No new local raw-data deletion is performed.

Conifers have five vegetation classes (foliage, three roundwood classes, one stem), versus seven in the previous broadleaf cases. Extraction validates class names and initial mass against each original deck and includes all vegetation/stem classes while excluding the contact ignitor. This applies the same bookkeeping definitions, not a physics change.

The11-state ignition-anchored cone and14-state free cone retain the existing fitting settings, bounds, >50C threshold, >=95%hot-cell coverage criterion and interpolation rules. The four water/fuel/gas/heating histories are identical between versions. Geometry between the six actual saved volumes is interpolated, never a measured3D field; masks, source times and brackets are retained. A free cone's apex is a geometric fit, not necessarily the physical origin of fire. Initial crown/stem outlines do not show burn state. Contact ignition lasts20s; sparse volumes cannot recover unsaved early plume shapes. Other material limitations remain those documented in CONE_COMPARISON_PREVIEW.md.

Twenty datasets and ten paired3D animations are written to data/conifer-cone-preview. Original previews are retained. No new simulations, model training, or conversion outside the selected ten. All raw and training data remain local.
