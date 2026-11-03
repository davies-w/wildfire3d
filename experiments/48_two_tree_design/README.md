# Two-tree sampled simulation design

Prepared 24-case pilot with cloud launch authorized on 2026-11-02. See `launch-record.json` for the frozen inputs and controller; private execution records contain the actual submission state. The user approved replacing the 180,000-case Cartesian product with 2,000 sampled examples on 2026-11-02.

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

## Cloud execution

`pilot_worker.py` runs four OpenMP threads per solve on Spot C3 machines. Four nominal-geometry cases (both species × both ignition families) run first on c3-standard-4. Only if all four finish successfully does the controller release the remaining 20 cases in parallel, on c3-highmem-4 for 32 GB RAM per worker. The larger-memory machine retains four threads and does not change the numerical inputs. The regional Spot quota was increased to 80 vCPUs for this launch.

Each case first runs cloud-only parser, initial wet-mass (1% tolerance), and portable restart checks through 0.15 seconds. These probe states are discarded. The full 180-second solve has a two-hour wall allowance, including snapshot overhead, within a three-hour Batch task limit. The controller enforces an approximately 3.1-hour VM lifetime, a four-hour queue/run deadline per wave, and cleanup of jobs/VMs/disks. Zero automatic Batch retries. Two waves could take several hours; no measured runtime for the new geometries is yet available.

Roughly every five minutes of solver wall time, the runner requests a graceful stop and uploads the stopped output/restart directory in hash-verified immutable chunks before resuming. A complete manifest is the commit marker; interrupted uploads are not usable snapshots. Abrupt Spot loss before the first snapshot can still lose that initial work. Recovery after eviction requires inspection and a unique continuation submission; it is not an automatic restart. Wall limits cannot be extended in place. Completed and incomplete outputs are retained, including restart files.

The restored image includes the same verified FDS binary as experiment 36. The build required restoring narrowly scoped source-read permission; rejected requests did not start builds or simulations. Input transport and the controller use unique `tree48/pilot01/` paths. Read-only readiness runs the same inventory checks as cleanup. A separate quota gate prevents bulk submission below 80 available Spot vCPUs.

Review post-source burning, mesh/domain comparisons, runtime and storage before bulk data generation. The finer runs test gas-grid resolution only; vegetation discretization is unchanged. Taller-tree cone-label scales and model mass normalization still require adjustment before model training. Financial records and raw operational status remain private. No neural training is part of this pilot.

## Controller correction

Pilot01 failed before solver startup because repeated writes to one status-object name required overwrite permission. All five objects were archived privately, all four briefly allocated VMs and disks were removed, and its exact read grant was removed after allocation-cost reconciliation. No case completed and no solver checkpoint existed. Pilot02 uses the same 24 decks, solver binary and worker code; only transport namespace and controller status names change. Status objects are immutable and uniquely timestamped. Readiness now performs two consecutive writes before launch. See `launch-record02.json`; current operational scripts are `monitor_pilot02.py` and `launch_pilot02.py`. Never restart pilot01.
