# Corrected two-case cone comparison

This fulfills the requested ignition-anchored cone versus freely fitted cone comparison for the same two cases. The earlier ellipsoid preview was an unrequested substitution and is retained separately, not treated as fulfillment.

The anchored cone is unchanged: 11 channels, four original water/fuel/gas/heating channels plus presence, unit xyz direction, axial length, end radius and peak temperature. Apex is a fixed ignition-location input.

The free cone adds apex xyz for 14 channels total. It uses the already investigated plus_horizontal_apex fits, with apex x/y bounded to the simulation domain, apex z from zero to tree height, tilt 0–90 degrees and azimuth -180–180 degrees. Three deterministic optimization seeds use a ranking subsample; extents are recalibrated on all hot cells to cover at least 95%. No global optimum is claimed. The fitted apex is a geometric parameter, NOT a physical combustion origin. Its proximity to a bound remains a fitting limitation.

Both retain the identical four original histories and six actual saved-volume samples. Intermediate spatial rows are interpolated, not measured volumes. Apex and extents interpolate linearly; direction uses normalized-linear interpolation. During appearance/disappearance the available active apex/direction is held while extents grow/shrink. Absent zero coordinates are sentinels, not ground locations. No extrapolation. Masks, bracketing times/weights, fixed inputs and first/next-state JSON are retained.

Animations read these datasets directly, with the anchored cone left and free cone right. Gray dots only show actual saved >50 C cells; wire shapes are not measured flame surfaces. Red star is fixed ignition location; blue cross is fitted apex. Green outlines are initial vegetation, not remaining fuel. Shapes may extend outside the simulated domain, where no raw observations exist. Oak has no >50 C cells at the six saved times; unsaved transients cannot be ruled out. Original grid/ignition/fuel limitations in SPATIAL_TRAINING_PREVIEW.md and original metadata remain applicable.

No new simulations, bulk conversion or raw-data deletion. Outputs are data/cone-comparison-preview/CASE/{cone,free_cone}, with paired comparison-3d.gif.
