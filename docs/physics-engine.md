# Which physics engine: the survey behind choosing FDS

Question: what open-source model can simulate fire at the scale of a single
property — a house, its garden, the fence, a few trees — in 3-D and in time?

Two things were ruled out early and are worth stating plainly:

- **Writing one.** A from-scratch model was built and then discarded. It is not
  in this repository. Surface-fire spread from empirical formulas and a
  hand-rolled ember/flame-front treatment is not a substitute for solving the
  flow, and the effort went into closures rather than physics. See
  `working-practices.md` for what was learned the hard way.
- **Operational fire-spread tools** (FARSITE, FlamMap, ELMFIRE). These are
  2-D-and-a-half landscape models. They answer "does fire reach the
  community", not "what happens to this building", which is the question here.

What follows is the survey behind the choice actually made, biased towards
**open-source** tools and **published equations** so the physics stays auditable.
Section 8 gives the verdict: **NIST FDS**.

---

## 1. The operationally important question

The US National Institute of Standards and Technology (NIST) summarises the
wildland–urban interface (WUI) problem as one of *fire dynamics and spread in WUI
fuels*, driving physics-based CFD model development. The empirical picture that
motivates modelling at the property scale:

* Direct and indirect **ember (firebrand) attack** was responsible for the
  ignition of roughly **two thirds** of destroyed homes in the case studied by
  the physics-based grassland-fire work of Linn and co-workers — that is, most
  homes are lost to *indirect* attack, not to the flame front arriving.
* When the first fire front arrived, the rate of structure ignitions peaked at
  about 21 per hour.

The practical consequence: **what happens when an ember lands on the fuel next to
your house is the dominant loss mechanism**, and it is the thing most worth
modelling well. On this evidence the ember → fuel-bed → spot-fire chain matters
at least as much as the flame front, which is why the cases here put embers,
landing surfaces and the walls behind them at the centre.

---

## 2. Surface fire spread: Rothermel and its descendants

**Rothermel (1972)**, *A mathematical model for predicting fire spread in
wildland fuels*, USDA Forest Service Research Paper INT-115.
The original. A steady-state energy balance on the flaming front producing a rate
of spread from fuel load, bed depth, surface-area-to-volume ratio, moisture,
mineral content, wind and slope.

**Andrews (2018)**, *The Rothermel surface fire spread model and associated
developments: a comprehensive explanation*, RMRS-GTR-371.
The best single reference for getting the equations right, including Albini's
1976 wind-factor adjustments.

**CSIRO Spark.** <https://research.csiro.au/spark/>
Open-source (Apache-2.0) toolkit for end-to-end wildfire simulation. Its model
library is a good sanity check, and it is the source of the metric form of the
Rothermel wind factor used here (u in m/min, σ in m⁻¹).

**ForeFire.** <https://github.com/forefireAPI/forefire>
Open-source (C++, LGPL) wildland fire spread engine using a front-tracking
(level-set-like) approach with multiple rate-of-spread models.

**ELMFIRE.** <https://github.com/lautenberger/elmfire> , <https://elmfire.io/>
*Eulerian Level set Model of FIRE spread.* Explicitly supports spotting (ember /
firebrand transport), smoke, and **structure-to-structure spread in the WUI**.
Public domain / open source.

**FARSITE / FlamMap / BehavePlus.** USDA FS. The classic operational
implementations of Rothermel. FARSITE introduced the Huygens elliptical
wavefront propagation still used widely; FDS's level-set spread model uses the
equivalent minimum-travel-time formulation.

**SimFire.** <https://github.com/mitrefireline/simfire>
Open-source Python wildfire simulator implementing the Rothermel model, aimed at
reinforcement-learning environments.

**PROPAGATOR.** Cellular-automata operational simulator with a published
fire-spotting module (Egorova, Trucchia et al.), including event-based ember
production/transport and secondary ignitions.

---

## 3. Firebrand transport and combustion

**Ember transport in plumes.**
A fast, physically based model of firebrand transport by bushfire plumes
(Agricultural and Forest Meteorology, 2023) decomposes the problem into: an
integral plume model, a model of turbulence within the plume, a probabilistic
ember-transport model, and a model of transport beneath the plume. The scheme used
here covers the "beneath the plume" part, with the updraft supplied by the
solver.

**The arxiv review of wildland fire and ember spread** (arXiv:2608.07761)
concludes that atmospheric conditions, surface boundary-layer processes,
background and plume-induced turbulence all strongly control ember transport and
landing patterns, and that the physics-based approach provides a solid base from
which to simplify. Notably, it argues ignition occurs in only a fraction of
embers, but this does not change the *distribution* of landing locations
significantly in the near field.

**Manzello and co-workers (NIST).** A long series of experimental papers on
firebrand generation, transport and deposition onto fuel beds, in both flaming
and glowing states. The standard reference for firebrand size and mass
distributions.

**Urban, Song, Fernandez-Pello et al. (2019–2021).** *Ignition of wildland fuels
by idealized firebrands* (Fire Safety Journal) and *Sensitivities of Porous Beds
and Plates to Ignition by Firebrands* (Frontiers in Mechanical Engineering 2021).
Key findings used here:
* **larger firebrands are more likely to ignite fuel beds** across a range of
  fuel moisture contents;
* the derived heat flux to the fuel bed sits within the range reported in the
  literature for firebrands;
* time-to-ignition and probability-of-ignition depend on bed structure and
  heater temperature, motivating the porous-bed rather than plate treatment.

**Yang, Peng, Urban, Huang et al. (2025).** *Computational study on the glowing
combustion of a wooden ember landing on a non-reacting substrate.* The burning
temperature and heat flux from a single ember are what determine the heat
transfer to the fuel bed, and there is a **minimum ember size** below which the
stored heat is insufficient to initiate ignition — a threshold that should be
reproduced deliberately rather than assumed away.

**Zvyagilskaya & Subbotin**, *Simulation of fuel bed ignition by wildland
firebrands* (International Journal of Wildland Fire, WF17083).
A 3-D mathematical model of fuel-bed ignition by glowing firebrands. Establishes
that (i) the heat stored in small brands is insufficient to initiate ignition,
(ii) temperature in the wood layer rises slightly at first before falling as
heat is lost, and (iii) above a critical size pyrolysis begins in the region
adjacent to the brand. This is the closest published analogue to the fuel-bed
model closest to this problem in the literature, and the behaviour it describes
— a size threshold, an early temperature bump, a plateau — is what an ember
landing on a fuel bed should show.

**Bakhshaii & Johnson**, *Spotting ignition of fuel beds by firebrands*, and the
WIT CFD/pyrolysis coupled models: a CFD gas phase coupled to a condensed-phase
heat-transfer and pyrolysis model, used to simulate ignition of a powdered
cellulose fuel bed by glowing pine embers.

---

## 4. Fuel-bed ignition thresholds

**McAllister, Finney, Cohen et al. (2010, 2011).** *Critical mass flux for
sustained flaming ignition of woody materials* — measured critical mass fluxes of
**1–3 g m⁻² s⁻¹**, increasing with heat flux and moisture content. Used here as
the gas-phase criterion (1.5 g m⁻² s⁻¹).

**Piloted ignition of cylindrical wildland fuels under irradiation** (Frontiers
in Mechanical Engineering, 2019). Establishes that under irradiation the ignition
temperature is elevated relative to the true pyrolysis temperature because only
the thin surface layer is pyrolysing; there is a roughly constant critical
irradiation. Supports the two-condition criterion used here.

**Ignition of wood under time-varying radiant exposures** (Fire Safety Journal):
the standard experimental basis for ignition time as a function of flux.

**The autoignition/piloted-ignition literature for building materials** gives the
facet thresholds used: **12.5 kW m⁻² for piloted ignition of wood and damage to
plastics**, with a minimum radiant flux for wood ignition as low as
**4.3 kW m⁻²** under ideal conditions, and pretreated wood not igniting below
**12 kW m⁻²** in the smouldering-ignition study of plywood. Metal roofs and
other Class-A assemblies tolerate far more (≈25 kW m⁻²).

---

## 5. Whole-property / WUI CFD

**FireFOAM.** A coupled fire–atmosphere model on the **OpenFOAM** platform
(open source, GPL), underpinned by large-eddy simulation with the Eddy Dissipation
Concept combustion model. Used for LES simulations of wind-driven wildfire
interaction with idealized structures in the WUI
(*Atmosphere* 12(1):21).

**FDS / WFDS.** NIST's Fire Dynamics Simulator and its wildland counterpart.
Physics-based CFD. Designed for compartment fires originally, extended to
vegetation.

**NIST Wildland–Urban Interface Fire Group.**
<https://www.nist.gov/el/fire-research-division-73300/wildland-urban-interface-fire-73305>
Provides data on fire dynamics and spread in WUI fuels explicitly to drive
physics-based CFD model development.

**PyroSim-based ember deposition studies.** Recent work (Combustion Science and
Technology, 2026) investigates transport and accumulation of non-combusting ember
particles over sample buildings, balconies and vegetation — establishing that
building *geometry* (balconies, roof valleys, wall junctions, fence lines)
controls where embers accumulate.

**Simulation of ember transport around urban structures**
(Modsim 2025, Cunningham et al., Australia) found less sensitivity to the layout
of solid structures than expected, but significant effects including channelling
of flow between structures, ember flux on portions of structures parallel to the
prevailing wind at ground level, and recirculation. Practical implication adopted
here: place the deck and the fence, which are real ember traps, and expose the
walls to a view-factor calculation rather than assuming uniform ember loading.

**WUI-NITY** (*Safety Science*, 2020), built on Unity3D, simulates and visualises
human behaviour and wildfire spread during evacuation — a reminder that the
property-scale model has to hand off to a life-safety model, which nothing here
attempts.

**A critical review of wildfire models and simulation tools for WUI** (NRC
Canada) frames the gap this project targets: a wildfire model may tell you
whether fire reaches a community but is less useful for determining the transfer
of fire *to* a structure.

---

## 6. Graphics / high-fidelity vegetation combustion

**Scintilla: Simulating Combustible Vegetation for Wildfires**
(ACM Transactions on Graphics, 2024). Simulates the interaction between
convection, combustion and heat transfer between vegetation, soil and
atmosphere, with a detailed representation of vegetation including branch
geometry, fuel moisture, and the distribution of grass, fine fuel and duff, plus
ignition, generation and transport of firebrands.

Notable because it is closest in *spirit* to this problem — a property/plot-scale
model with grass, fine fuel and duff as distinct entities — while being a
rendering paper rather than an operational physics model.

---

## 7. Findings that drove concrete modelling decisions

Concrete decisions traced back to the literature:

| decision | source |
|---|---|
| log-normal firebrand size spectrum | Manzello; Urban et al. |
| critical volatile mass flux 1.5 g m⁻² s⁻¹ | McAllister et al. |
| ignition needs both a temperature and a mass-flux criterion | Frontiers 2019 |
| emergent minimum firebrand size | Yang et al. 2025; Zvyagilskaya & Subbotin |
| thin-disc geometry and char density, not spheres | firebrand terminal-velocity measurements |
| two-dimensional, not one-dimensional, fuel bed | porous-bed vs plate results, Urban et al. 2021 |
| facet thresholds 7–25 kW m⁻² | piloted-ignition literature |
| no damage accumulation below q_crit | steady-state behaviour of inert solids under radiation |
| Rothermel with the metric wind factor | Rothermel 1972; Andrews 2018; CSIRO Spark |
| minimum-travel-time fire growth | FARSITE / ELMFIRE lineage |
| view-factor radiation, solid-flame model | standard bushfire radiant-heat practice |
| embers dominate loss | NIST WUI; Linn et al. |

---

## 8. Open-source tools worth knowing about

| tool | language | licence | what it is |
|---|---|---|---|
| Spark | Python | Apache-2.0 | end-to-end wildfire simulation toolkit |
| ELMFIRE | C++ | public domain | level-set fire spread with spotting and WUI |
| ForeFire | C++ | LGPL | front-tracking fire spread engine |
| SimFire | Python | MIT | Rothermel simulator for RL |
| FireFOAM (OpenFOAM) | C++ | GPL | fire–atmosphere LES CFD |
| FDS / WFDS | Fortran/C | public domain | NIST fire dynamics, CFD |
| PROPAGATOR | Python | open | cellular-automata operational simulator |


**The choice: FDS / WFDS.** For this use case it is the only open-source option
that gives 3-D transient CFD, level-set vegetation spread, Lagrangian firebrands
and surface ignition in one solver, and it runs on a laptop. FireFOAM is the
closest alternative and is a credible one, but FDS ships a wildland fuel model
and an ember model out of the box, is public domain, and is far better
documented for this kind of case.

What FDS is good and not good at, measured rather than assumed, is in
`working-practices.md`. The short version: it is excellent on *what happens
around* a building in a fire, and comparatively weak on *how the vegetation
burns* unless you can afford 0.05 m cells.
