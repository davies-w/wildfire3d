# Two-tree sampled simulation design

Prepared design and pilot input decks; no cloud jobs or reservations. The user approved replacing the 180,000-case Cartesian product with 2,000 sampled examples on 2026-11-02.

- Type1 Ponderosa pine: total height18–22m and crown radius1.5–5.5m, both at1m increments; crown base fixed6m.
- Type3 Blue gum eucalyptus: total height22–26m and crown radius3.5–7.5m, both at1m increments; crown base fixed12m.
- Radius means half the total x footprint width. Both horizontal coordinates and crown sizes scale together; vertical crown coordinates scale above the fixed crown base. Clump layout is preserved. Union overlaps must not multiply fuel.
- 25 geometries/type,50 total;40 examples/geometry,1,000/type. Each geometry has20 base-only and20 crown-only ignition examples; never both in one example.
- Base heights0.25/0.75/1.25m; crown levels10/50/90% up the crown. Eight compass directions. Every angle occurs5times per geometry across both families. Each family samples20distinct locations out of24, each height6or7times. Not all48locations are used in each geometry.
- Each family has4examples at each wind1–5m/s and each moisture6/12/18/24/30%. Loading0.7/1/1.3 is balanced to6or7examples/family. Pairings are reproducibly randomized using seed4803516; this covers marginal values, not every interaction.
- One imposed20-second heating patch per example, including low trunk cases. No grass fuel is added. For separated eucalyptus clumps, crown contact is the actual foliage boundary point facing the requested compass direction in that horizontal slice; it is not necessarily a radial ray from the trunk. Exact local coordinates are recorded.

`prepare.py` creates50geometry definitions and a compressed2,000-case manifest and checks counts, unique ignition locations, family balance, angular coverage and wind coverage. The earlier180,000-case output is superseded. No simulations from that plan ran.

The model retains8historical timesteps of10values and feedback of all10predictions. Planned extra external features describe geometry, ignition coordinates/family and five one-hot tree IDs. Only IDs1and3are trained in this initial dataset. Same1/8/16/32/64/90curriculum at epochs1/21/41/61/110/130 is retained as a starting protocol. Splits must be fixed before fitting, with repeated configurations grouped and geometry-combination holdouts considered.

## Prepared pilot

`prepare_pilot.py` produces 24 FDS decks: 20 distinct cases from the approved 2,000-case manifest, plus four numerical comparisons. For each species, the four radius/height corners and nominal geometry each receive one base and one crown ignition. Environmental values are sampled from existing manifest rows; this small pilot does not cover all interactions.

Each species also has one crown-ignition case repeated with a larger domain and with a finer gas grid. Baseline: 48 × 32 × 40 m at 0.5 m (491,520 cells). Larger domain: 64 × 48 × 56 m at 0.5 m. Fine grid: original domain at 0.25 m (3,932,160 cells). Vegetation sampling stays fixed, so the fine run tests the gas grid only. Duration is 180 seconds. Outputs include temperature volumes every 2 seconds, fuel-particle outputs, mass and fuel-vapour devices.

Crown fuel uses the previous four generic vegetation classes and dry bulk densities. Overlapping crowns form a union, estimated with 0.125 m subcells; one weighted representative per occupied 0.5 m cell and fuel class approximates that volume. This is not resolved individual foliage. Crown loading multipliers do not alter main-stem mass.

Trunks and drawn main branches now burn as static cylindrical thermal particles with generic vegetation/wood chemistry and density 500 kg/m³. They are not resolved solid airflow obstacles, have no bark layers or species-specific chemistry, and use the same moisture fraction as the crown. Branch-junction cylinder overlaps are not subtracted, slightly overcounting wood at those junctions. Thus species names describe abstract geometry, not validated species fire behaviour. Embers are not modeled.

Ignition uses 1,600 imposed heating particles in a constant 0.4 × 0.4 m tangent patch, with the previous 1500 °C setting, HRRPUA 60 and 20-second ramp. This changes the previous arc-shaped footprint; it does not preserve total delivered heat, which depends on coupling. Base cases contain no grass. Crown patches touch represented foliage. Imposed heating is not evidence of self-sustained ignition; that must be assessed after the source switches off.

Offline checks pass for all 24 decks: geometry membership, ignition contact, boundaries, input structure, and independent fuel-mass accounting. They do NOT establish FDS parser acceptance, correct runtime mass, restart behaviour, successful ignition or sufficient resolution/domain/time horizon.

`pilot_worker.py` is a draft cloud-only runner for parser/mass/restart probes and a full solve with a two-hour wall limit. It is not a deployed launch package. It archives evidence on handled exit, but abrupt Spot loss can lose the current case; no remote periodic restart preservation is claimed. No local solver was run.

**Before launch:** rebuild/verify the solver image (the former solver36 digest was absent from the registry at preparation), package immutable input transport, verify cloud-only parser/mass/restart probes, and configure resource cleanup and the spending cap. Review pilot runtime, post-source burning, boundary effects, fine-grid differences and output storage before the 2,000-case campaign. Taller-tree cone-label scales and model mass normalization also require adjustment before model training. Cost estimates and the spending ledger remain private.
