# Thermal and spatial-state observability audit

User authorized three stages: audit thermal labels; matched three-state versus four-state training; evaluate whether spatial information is justified. No new FDS or local training.

All520 histories have four-class remaining-mass-weighted particle surface temperature. Pinned FDS source audit in attempt14 identifies PARTICLE TEMPERATURE as TMP_F: surface temperature, not internal material temperature. Neither internal temperature profiles nor frame-by-frame composition-specific heat capacity are available in these snapshots. Therefore no true stored thermal energy in joules is asserted.

Candidate fourth state is sum(m_remaining * (T_surface -20C))/initial_total_mass. It has Kelvin units and is a surface-heating index, not actual mean remaining-material temperature or energy. Fixed initial mass denominator avoids a shrinking denominator exaggerating residual heating. It mixes wet vegetation, char and ash in remaining mass; char remains inert for the original fuel accounting, but measured char/ash surface temperature contributes to this proxy. No negative values are clipped. Across520 histories the index ranges−0.356 to341.0K; peak median136.9K. Initial values are within5e-6K of zero. These are approximate two-second samples aligned to particle frames within0.21s.

Existing gas hot-plume centroid is defined in only36.9% of snapshots; it includes imposed-source heating and is not anchored to the crown. Gas temperature-excess integral has K m³ units, not joules. Neither centroid direction nor elongation establishes directional heat transfer. Do not introduce a heat-flow arrow from these summaries.

Stage2 is attempt20: matched GRU control versus fourth surface-heating state on all520 histories and existing grouped10fold rotations. Stage3 will separately examine particle heating spatial moments relative to measured initial vegetation mass centroid; these represent heating location, not heat-flux direction. The scalar comparison's validation outcomes, not its tests, govern whether a further spatial comparison is justified. All raw source and results retained.
