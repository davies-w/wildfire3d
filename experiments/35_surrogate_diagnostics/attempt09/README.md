# Original-physics audit: why HOT regions disappear

Read-only audit of all472 archived new-geometry FDS runs, with no new simulation, training or paid job. This checks original global heat-release CSVs, vegetation mass/fuel-vapor devices, raw temperature slice records and viewer labels. Every raw archive and input deck SHA256 matched its preserved metadata.

## Finding

There is substantial combustion after the artificial ignition ends around20.1s, followed by rapid decay. Calling the dataset merely heating/cooling or saying the networks were all trained to do nothing was too broad. It contains short-duration burning and its cooling tail. Five of the ten selected time models nevertheless have all-cold training labels. This is not sustained burning through180s, and does not establish realistic vegetation-fire behavior.

Each entry below is the median across472 trajectories of the time-averaged original CSV quantity. Replicate trajectories are counted individually here; these are descriptive physical audits, not configuration-balanced model scores.

| Window | Gas-phase HRR | Solid-oxidation HRR |
|---|---:|---:|
|21–40s|4175kW|2466kW|
|40–60s|31.52kW|222.25kW|
|60–80s|1.287kW|64.81kW|
|80–100s|0.0930kW|13.57kW|
|100–120s|0.0147kW|0.729kW|
|120–180s|0.00528kW|0.000513kW|

HRR and HRR_OX are retained separately. Late gas-phase HRR averages at most0.0435kW across any run; solid oxidation can persist more strongly in a few cases (maximum120–180s mean5.19kW). Thus “every reaction has stopped” would be false. Fuel-vapor release in120–180s is tiny: median0.0000186kg over the entire60s window. Large late hot plumes are absent in this fixed domain.

## Material changes

The median reduction in represented particle mass from initial geometry to180s is48.2%, ranging1.66–98.14%; the strongest post-source runs lose roughly90–97%. This is NOT a pure burned-dry-fuel fraction: moisture loss, released fuel gases, solid reaction products and retained char/ash affect particle mass. Original mass and fuel-vapor histories are preserved per case. The DEVC CSV records zero mass at t=0 before initialization; initial mass therefore comes from the archived weighted-particle geometry, not that zero. Remaining mass does not identify how much reactive fuel is left. Some runs substantially deplete material; others retain most material and nevertheless become weak. This audit alone does not distinguish the contributions of fuel exhaustion, moisture, heat loss, kinetics and geometry to each fire's decline.

## Temperature extraction checks

An independent Fortran-record decoder exactly reproduces all91 packed temperature masks for every one of472 runs (42,952 snapshots), not just the ten viewer times. No missing late viewer snapshots were found. The official installed fds2ascii independently agrees for a strong-fire example x32_066_s0 over120–124s within0.0005°C (CSV print precision).

Important qualification: the viewer uses physical cell-center indices1..48,1..32,1..32. The raw49×33×33 record also contains index-zero boundary values. At nominal120s, interpolated physical-cell peaks have median21.44°C and maximum46.18°C. Including boundary records instead gives a maximum62.39°C, with88runs above50°C. Therefore the earlier wording “every value in the domain is below50°C” was too absolute. Those excluded boundary records are not additional physical gas-cell centers or a missing hot plume. In the official-converter example the hottest extra value is at z-index0; the raw-record average peak47.506°C differs from the physical-cell average peak26.456°C. The boundary record is not interpreted here as a measured solid-ground temperature.

The local FDS source DUMP_SLCF/GAS_PHASE_OUTPUT confirms cell-centered output evaluates array indices including boundary indices and temperature returns TMP minus the Celsius offset. The model/viewer use the interior cell-center extent. FDS distinguishes solid-oxidation heat in HRR_OX; see https://github.com/firemodels/fds/issues/14362 and the official source https://github.com/firemodels/fds/blob/master/Source/dump.f90.

## Decision and limitations

The disappearing HOT regions reflect original physical-cell outputs and collapse of gas-phase burning, not a viewer dropout. Dense sampling of20–80s would cover more of this dataset's active burning, but is not a substitute for validating the simulated fire. No model or simulation change is made by this audit. Before more training, diagnose why duration varies and whether the intended application requires longer-lived burning/spread.

Generic3m-wide conical crowns4/6/8/10m tall above2m,1600weightedparticles,0.5m grid24×16×16m,180s. Artificial1500°C contact ignition with prescribed HRR through20s, ramped off by20.1s; no trunks/buildings/embers. HRR during ignition includes imposed burning and cannot be attributed wholly to vegetation. Previously examined data, no real-world physical validation. Temperature threshold masks are HOT gas, not flame geometry.
