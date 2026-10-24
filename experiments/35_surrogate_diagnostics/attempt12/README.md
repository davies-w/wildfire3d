# Full compact-state dataset preparation

User explicitly authorized reshuffling the full dataset for grouped ten-fold sequence learning. This stage inventories all 520 histories: 472 new histories and 48 reused legacy histories. Former test labels are retained as provenance, not advertised as pristine tests. All 520 raw archive paths exist locally. Content/schema compatibility is verified during extraction before assigning folds. No model is trained here.

The same compact-state extraction as attempt11 is used, with one archive decoded at a time and only temporary decoded volumes removed. Original raw archives and prior outputs are preserved. New archive SHA256 values are checked against the verified archive inventory; legacy SHA256 values are recorded during extraction. Particle alignment, six gas channels, domain and horizon are checked. Failures stop extraction rather than silently excluding histories. Cached complete case JSON permits resumption. No new FDS, cloud compute or optimizer.

Material totals include water and reaction products, not separate dry fuel/water/char. Plume covariance and centroid are lossy hot-gas summaries, not heat-energy vectors. Gas thermal energy and directional radiative flux remain unavailable. Legacy geometry differs and will remain identified in evaluation. All quantities retain actual timestamps.
