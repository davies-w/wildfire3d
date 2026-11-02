# Two-tree sampled simulation design

Prepared design only: no executable FDS decks, cloud jobs or reservations. The user approved replacing the 180,000-case Cartesian product with 2,000 sampled examples on 2026-11-02.

- Type1 Ponderosa pine: total height18–22m and crown radius1.5–5.5m, both at1m increments; crown base fixed6m.
- Type3 Blue gum eucalyptus: total height22–26m and crown radius3.5–7.5m, both at1m increments; crown base fixed12m.
- Radius means half the total x footprint width. Both horizontal coordinates and crown sizes scale together; vertical crown coordinates scale above the fixed crown base. Clump layout is preserved. Union overlaps must not multiply fuel.
- 25 geometries/type,50 total;40 examples/geometry,1,000/type. Each geometry has20 base-only and20 crown-only ignition examples; never both in one example.
- Base heights0.25/0.75/1.25m; crown levels10/50/90% up the crown. Eight compass directions. Every angle occurs5times per geometry across both families. Each family samples20distinct locations out of24, each height6or7times. Not all48locations are used in each geometry.
- Each family has4examples at each wind1–5m/s and each moisture6/12/18/24/30%. Loading0.7/1/1.3 is balanced to6or7examples/family. Pairings are reproducibly randomized using seed4803516; this covers marginal values, not every interaction.
- One imposed20-second heating patch per example, including low trunk cases. No grass fuel is added. For separated eucalyptus clumps, crown contact is the actual foliage boundary point facing the requested compass direction in that horizontal slice; it is not necessarily a radial ray from the trunk. Exact local coordinates are recorded.

`prepare.py` creates50geometry definitions and a compressed2,000-case manifest and checks counts, unique ignition locations, family balance, angular coverage and wind coverage. The earlier180,000-case output is superseded. No simulations from that plan ran.

The model retains8historical timesteps of10values and feedback of all10predictions. Planned extra external features describe geometry, ignition coordinates/family and five one-hot tree IDs. Only IDs1and3are trained in this initial dataset. Same1/8/16/32/64/90curriculum at epochs1/21/41/61/110/130 is retained as a starting protocol. Splits must be fixed before fitting, with repeated configurations grouped and geometry-combination holdouts considered.

Remaining preflight: executable source patch geometry/power and contact validation, stem/bark representation, crown fuel assignment, mesh/domain sensitivity and cone-label scaling for taller trees. Draft48x32x40m domain at0.5m has491,520cells,10times the prior domain; it is not yet proven sufficient. The proposed180-second horizon also needs checking. A small timing/physics pilot should precede bulk execution. Cost estimates and the spending ledger remain private.
