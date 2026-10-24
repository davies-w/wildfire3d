# Audit of water, fuel and heating observability

Local read-only audit of all 520 raw simulation archives; no simulation, training, architecture or state definition changed. All archives record FDS revision ff928dbf68a2623ced3a007be75391c6dc6c9f90. Exact official source URLs and hashes are in source-evidence.json. Raw inputs remain unchanged.

## Findings

All 520 have initial dry-basis moisture, four vegetation-class mass records, four class-specific fuel-vapor release records, and global MLR_WATER VAPOR. The particle outputs also contain surface temperature, incident heat flux and convective heat flux. FDS PARTICLE TEMPERATURE is TMP_F, a surface value, not the internal temperature distribution. These can support a coarse heating indicator without making exact temperature an output requirement; no indicator or threshold is selected here.

The earlier blanket statement that remaining water was unavailable was too strong. It is not directly exported as a remaining-water history, but can be reconstructed approximately from initial water minus cumulative water release. Official pinned wall.f90 accumulates particle surface species release into M_DOT; dump.f90 time-averages that accumulated release for HRR CSV output. This water-release column is not ambient humidity or water generated later by gas combustion. The decks use vegetation evaporation as the water source; their vegetation pyrolysis releases FUEL VAPOR, and char oxidation releases PRODUCTS/AIR.

For dry-basis moisture m and initial saved weighted particle mass M0, initial water = M0*m/(1+m), initial dry vegetation = M0/(1+m), matching read.f90's moisture mass fraction. Remaining water estimate = initial water minus sum(MLR_WATER_VAPOR[i] * (t[i]-t[i-1])). Use interval averages, not trapezoidal integration of the HRR CSV. The first device mass is zero before particle insertion, so it must NOT be used as initial mass; first saved particle mass is used instead. Initial particle timestamps are recorded per case.

All 520 water reconstructions stay within bounds to a maximum overdraw of 0.01015% of initial water (small numerical/sampling discrepancy); none exceeds 1%. No clipping hides this discrepancy. This is a mass-budget plausibility check, not independent validation of remaining-water truth. No per-class water-release devices are saved, so this supports a whole-tree water total, not class-specific drying histories.

All 520 decks use vegetation -> 0.75 fuel vapor + 0.25 char. Integrating the four vegetation-specific fuel-vapor device rates and dividing by 0.75 estimates consumed unreacted vegetation. These devices exclude the contact ignitor's fuel release, unlike a global fuel total. Device rates are sampled, so trapezoidal integration is approximate. All 520 final unreacted-vegetation estimates are nonnegative. Subtracting estimated water and unreacted vegetation from saved final total mass leaves nonnegative residual solid material in every case. This residual mixes char and ash: it is NOT all burnable fuel. Separate remaining char and ash histories have not been established by this audit. Restart files exist for all cases, but their contents were not decoded here and they are not a 91-frame material-composition history.

## Decision

The archives support initial moisture, estimated remaining whole-tree water, estimated remaining unreacted vegetation, measured burning rate and coarse heating evidence. They do not yet provide validated remaining total combustible fuel including char. Exact gas fields or gas temperature outputs are not required by this audit. No new model or additional features are approved or launched. Before using reconstructed values as training targets, quantify integration/mass closure over time and explicitly decide whether char oxidation belongs in the requested burnout model. The count of model state variables is still undecided.

These are generic conical crowns, artificial ignition for 20 seconds, 0.5 m mesh, no trunks/buildings/embers. Reconstructing bookkeeping variables does not physically validate the simulated drying or burning model.

Evidence: data/summary.json and 520 per-history audit JSONs, raw archive paths, recorded source revision, source-evidence.json. All calculations are reproducible with the DVC audit stage.
