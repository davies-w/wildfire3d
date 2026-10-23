# Why the tree-burning surrogate has not worked yet

Research and implementation review, 23 October 2026. Repository examined at `3422c4b`. This review launches no training, changes no frozen experiment, and makes no new compute reservation.

## Conclusion

We have not demonstrated that chaos or insufficient simulations is preventing success. We have demonstrated that several of our training objectives and reported aggregate scores can improve while the model fails to reproduce burning. We also moved between materially different tasks without maintaining a clear acceptance test for the original goal.

The present result is a useful predictor of hot-gas regions at particular times, especially around 20 seconds. It is not yet a surrogate for ignition, heat generation, fuel evolution and burnout. The literature supports pursuing that goal, but does not identify a universally correct architecture or show that an arbitrary number of simulations guarantees success.

The strongest next step is a controlled continuous-field modeling program with a fixed spatial backbone, explicit physical targets and staged fitting/rollout tests. It should reuse the existing data before commissioning more simulations. A learned state-evolution model is a justified candidate for the long-term goal; its state, initialization and autonomous rollout must be specified and tested. Naming it a U-Net, neural operator or recurrent model would not establish that it works.

## What the relevant papers actually solve

The following comparisons come from the papers' methods and results, not just their abstracts. Short summaries emphasize differences that affect transfer to this project. Published studies and preprints are distinguished.

### Wu, Wang and Luo, Energy and AI, 2024 — turbulent reacting-flow forecasting

Their SimVP spatial/temporal encoder–translator–decoder consumes ten physical-field frames and predicts ten more, then runs autoregressively. The cavity study uses 54 training and ten test operating conditions. Its LES study uses ten training and four test inlet temperatures, with two-dimensional planes extracted from three-dimensional simulations. Targets include thermochemical and flow fields. Training with unrolled predictions or input noise improves long forecasts. LES evaluation starts from ten true frames of an established flame; it is not cold-start ignition from static conditions. Mean and RMS statistics supplement instantaneous comparisons, and fluctuation errors remain. This is evidence for physical-state history and rollout-aware training, not evidence that a particular network can generate a tree's combustion source from nothing.

[Paper and full text](https://discovery.ucl.ac.uk/id/eprint/10185732/1/1-s2.0-S2666546823001052-main.pdf), sections 2–4; [DOI](https://doi.org/10.1016/j.egyai.2023.100333).

### Baykan et al., 2026 preprint — transient counterflow flames

A convolutional autoencoder compresses 21 thermochemical fields on a 256×256 two-dimensional grid; a neural ODE evolves the six-dimensional latent state. Five training inlet velocities and eight unseen conditions define a canonical laminar problem. Reconstruction and evolution are trained separately. Small temperature errors at trained conditions do not extend uniformly: reported unseen-condition temperature errors include approximately 25–31%, and some species are much harder. This supports testing whether a representation can reconstruct the fields before asking it to evolve them. It does not establish that six latent variables suffice for turbulent vegetation burning, or that its reported favorable errors are universal.

[Full preprint](https://arxiv.org/html/2603.15038v1), model/training sections and error tables. This is not treated as settled peer-reviewed evidence.

### Panayis et al., Simvue, 2025 preprint — an FDS temperature-map emulator

A U-Net is trained on 200 building-fire simulations, with 50 validation cases, using different fire locations. The source follows a prescribed growth curve reaching 1 MW. The surrogate outputs temperature on five horizontal planes at 20 minutes, rather than a complete three-dimensional ignition-to-burnout history. This is a useful counterexample to the claim that direct setup-to-snapshot prediction is inherently wrong: it can work. It is also a narrower problem than learning vegetation heat production and evolving fuel. The paper's broad discussion of fire simulation should not be confused with the specific demonstrated surrogate task.

[Full preprint](https://arxiv.org/html/2509.26139v1), sections 3 and 6.

### Buffington et al., Fire Technology, 2021 — transient compartment temperatures

The network is supplied a heat-release-rate history and predicts a temperature history at a thermocouple location; separate networks represent 17 locations. The study uses CFAST pretraining and FDS training, with held-out heat-release curves. It demonstrates accurate, rapid sensor-temperature emulation. Crucially, the heat source is supplied to the temperature emulator. That removes a major part of our task: determining how wet vegetation heats, releases gases, burns and stops burning. Sparse sensor histories also impose a different reconstruction burden from six complete three-dimensional fields.

[Full accepted paper](https://par.nsf.gov/servlets/purl/10381196), methods and transfer-learning experiments; [DOI](https://doi.org/10.1007/s10694-020-01037-2).

### Hodges, Lattimer and Luxbacher, Fire Safety Journal, 2019 — compartment-field reconstruction

A transpose-convolutional network reconstructs temperature and velocity distributions from coarse zone information. The study includes 1,333 FDS simulations, prescribed fire strengths, and simplified compartment boundaries. In the training construction, coarse inputs are derived from CFD, and targets are two-dimensional planes with temporal averaging. Thus this is strong evidence for learning spatial reconstruction, but not a demonstration of autonomous, instantaneous, full-volume vegetation combustion. Supplied coarse physical information and averaging both materially change the problem.

[Full accepted paper](https://stacks.cdc.gov/view/cdc/207122/cdc_207122_DS1.pdf), sections 2–3; [DOI](https://doi.org/10.1016/j.firesaf.2019.102854).

### Ohana et al., The Well, NeurIPS 2024 — cross-physics surrogate benchmarking

Across diverse physical datasets, U-Net variants and Fourier neural operators do not have a universal winner. The benchmark separates short prediction errors from rollout performance and uses variance-scaled errors to expose failures hidden by field magnitude or spatial means. A model approaching a simple late-time state can receive favorable errors without having captured the preceding dynamics. This supports keeping a credible convolutional baseline and evaluating physical fields and long rollouts separately; it does not justify switching architecture solely because another family is fashionable.

[Full paper](https://arxiv.org/html/2412.00568v1), benchmark results and metrics appendix; [official implementation](https://github.com/PolymathicAI/the_well).

### Kochkov et al., PNAS, 2021 — learned components inside a fluid solver

Convolutional networks learn local numerical approximations inside a conservative fluid solver. Training includes unrolled predictions, while evaluation separates short-time agreement, long-time statistics and stability. Their two-dimensional turbulence eventually loses phase agreement with the reference but can retain an accurate energy spectrum. This demonstrates why chaos is compatible with useful surrogates. It also illustrates a more constrained alternative to replacing everything with a neural network. It is not a reacting, multiphase vegetation model, and our correction to another neural network is not equivalent to retaining a physical solver.

[Full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8166023/), Methods and Results; [DOI](https://doi.org/10.1073/pnas.2101784118).

### Related titles that should not drive the design

A wildfire diffusion model examined here learns from a stochastic cellular automaton with burning/burned landscape states. That is a different target from FDS gas and vegetation physics. Its success does not establish a reason to use diffusion for this dataset. [Yu et al., GMD, 2026](https://gmd.copernicus.org/articles/19/1027/2026/), abstract and model description.

A multiscale reacting-flow FNO paper was also located, but only its abstract/introduction were accessible. Its detailed training and generalization claims are not used as evidence for choosing our architecture. [Zhang et al., Proceedings of the Combustion Institute, 2024](https://doi.org/10.1016/j.proci.2024.105714).

## What our own evidence establishes

### 1. The data contain combustion, but the ten-time classification task discards much of the goal

The independent raw-output audit found substantial heat generation after the imposed igniter turns off. Across 472 runs, the median run's window-mean gas-phase heat release is about 4,175 kW during 21–40 seconds, falling to 31.5 kW during 40–60 seconds. Solid-oxidation heat persists differently and is reported separately. Calling the dataset merely heating/cooling, or saying every network learned nothing, was too broad.

Conversely, five of the ten selected classifier times have entirely cold training labels. Successfully predicting those masks does not demonstrate fuel consumption or burnout. HOT means gas temperature above 50°C; it does not mean flame, combustion rate, remaining fuel or solid temperature. The visual disappearance was checked against raw FDS records and is not missing viewer data.

Evidence: [physics-audit README](../experiments/35_surrogate_diagnostics/attempt09/README.md), [audit summary](../experiments/35_surrogate_diagnostics/attempt09/results/summary.json).

### 2. The objective could improve while burning stayed wrong

For the coordinate model on one trajectory, matched post-igniter comparisons give:

| Quantity | Constant/background baseline | Trained coordinate model |
|---|---:|---:|
| Whole-volume normalized objective | 0.110424 | 0.062210 |
| Hot-region temperature MAE | 88.91°C | 61.36°C |
| Burning-region heat-release-density MAE | 12.552 kW/m³ | 12.477 kW/m³ |

The model's whole-volume temperature MAE was only 0.1785°C, while its total heat-release relative L1 error was 99.43%. Average objective improvement of 43.7% therefore did not mean it learned burning. Only 0.1371% of post-source cells exceeded 50°C and 0.2588% exceeded the heat-release-density threshold. Its heat-release channel error was worse than the constant baseline under that channel's own encoded objective.

This demonstrates objective/metric mismatch. It does not prove that every unweighted loss must fail or that a specific weighting scheme will solve it. For fully specified deterministic inputs and sufficient capacity, rarity alone does not mathematically force a zero prediction. In our finite models and optimization runs, it made a poor physical prediction inexpensive under the aggregate objective.

Evidence: [baseline audit](../experiments/35_surrogate_diagnostics/attempt06/results/baseline-audit.json), [analysis](../experiments/35_surrogate_diagnostics/attempt06/results/analysis.json), [final report](../experiments/35_surrogate_diagnostics/FINAL_REPORT.md).

### 3. There was a real gradient obstruction, but removing it did not repair fitting

The earlier GeometryCNN clamped encoded heat release before calculating training loss. Where its raw output was negative, the direct derivative through the clamp was zero. The saved-model audit demonstrated this on the sampled fields. The controlled raw-output comparison removed that obstruction but still left roughly 100% training heat-release error. The clamp was a defect in learnability, not a proven complete explanation of failure.

Shared layers can still change a clamped channel indirectly through other channels. Sparse-objective behavior, optimization and representation remain possible contributors. Their relative causal importance has not been isolated.

Evidence: [clamp audit](../experiments/35_surrogate_diagnostics/attempt04/results/output-clamp-audit.json), [controlled comparison](../experiments/35_surrogate_diagnostics/attempt05/results/analysis.json), [GeometryCNN](../experiments/32_tree_expansion/geometry_model.py).

### 4. The spatial classifier shows that useful structure is learnable

At 20 seconds the final HOT U-Net obtained training F1 0.892 and validation F1 0.726 at the frozen 0.5 threshold. Validation precision/recall were 0.652/0.821; exact score analysis gave ROC AUC 0.945 and average precision 0.787. These are meaningful signals from the existing conditions and geometry.

They do not establish accurate temperatures, heat release or time evolution. Falling training BCE and rising validation BCE expose a generalization problem under the loss, even where F1 improves. The active-time models reached their epoch cap without satisfying the declared plateau criterion. We must not call them converged or assume extending epochs will fix them.

Evidence: [20-second summary](../experiments/35_surrogate_diagnostics/attempt07/results/time20-summary.json), [ROC/PR results](../experiments/35_surrogate_diagnostics/attempt07/results/time20-roc.json), [all-time analysis](../experiments/35_surrogate_diagnostics/attempt07/results/analysis.json).

### 5. Corrections to our account of earlier experiments

It is incorrect to say we never modeled evolving material state. Experiment 32's recurrent hybrid consumed previous gas fields, geometry, imposed-source information, moisture, coarse particle mass and particle temperature. However, its gas prediction was a bounded correction, `snapshot + 0.5*tanh(correction)`, around a separately trained snapshot model. Its material grid was 2 m, versus 0.5 m for gas fields. It was not an unrestricted learned time-step solver.

It received 1,600 sampled trajectory updates over 400 training configurations: four draws per configuration in expectation, not four complete guaranteed epochs. Gradients were truncated every eight frames. Validation objective was still decreasing at the final recorded checkpoint, from approximately 0.1200 initially to 0.1144. This does not establish adequate optimization or a failure of state-based models as a class.

It is also incorrect to say no earlier models used validation checkpoint selection. Experiment 32 selected both snapshot and hybrid checkpoints by validation objective. The later HOT experiment used a frozen final-epoch/threshold reporting protocol instead of selecting maximum validation F1. The original experiment-32 fresh tests were generated after predictions were frozen; subsequent examination means those cases are no longer pristine for future research informed by their results.

Evidence: [sequence architecture](../experiments/32_tree_expansion/sequence.py), [training and selection](../experiments/32_tree_expansion/learning_worker.py), [learning histories](../experiments/32_tree_expansion/results/learning.json).

## Is data quantity the bottleneck?

We have 360 distinct new-geometry training configurations with 91 saved times each: 32,760 primary-run volumetric frames. Additional seed replicates and legacy cases exist. This is enough to require a serious baseline and controlled learning-curve study before blaming lack of data. It is not 32,760 independent fire configurations, and the many cells within a frame are highly related.

Some successful papers use fewer operating conditions, but often receive recent true physical states, prescribed heat release, averaged targets or reduced-dimensional outputs. Their sample counts cannot prove that 360 is either sufficient or insufficient for our broader task.

There are two different information questions:

- A direct map from complete initial conditions and time to a specified output is legitimate. It need not receive the intermediate fuel state to be mathematically meaningful. The challenge is whether our chosen conditions specify the desired deterministic output or only a distribution over particle/turbulence realizations.
- A state-to-state model needs a state/history sufficient to predict the next step. Our six gas channels omit some species information, while archived particle data include mass and temperature but do not automatically provide separately resolved dry fuel, water and char. We must audit available states rather than assume either that all information is present or that new simulations are mandatory.

The failure to fit one known realization cannot be explained away by unpredictability between different realizations. Chaos matters when demanding long-horizon pointwise agreement across unobserved initial perturbations. It does not excuse getting the heat-release curve, integrated energy or known training example almost completely wrong. Existing replicates can measure variability, but their finite count and timestamp jitter do not establish a rigorous irreducible error floor.

## A coherent route forward

This is a proposed experimental program, not a claim that the next model is already validated. No run is authorized or submitted by this review itself.

### Keep the backbone fixed and separate the questions

Retain a multiscale three-dimensional U-Net as the spatial baseline. The current binary models remain frozen. A separate continuous-output experiment should test temperature, heat release and the other gas fields with an explicit output parameterization, channel scaling and burning-region evaluation. Do not change the backbone, data coverage and objective simultaneously.

First demonstrate fitting of one and then a small group of complete training histories under the physical metrics below. Audit gradients, channel contributions and reconstruction resolution before a large run. An aggregate normalized loss threshold is not a sufficient success condition. If the model cannot reconstruct the supplied fields, adding recurrence, more cases or a more elaborate solver will obscure the problem.

### Define a state-evolution candidate for the full burning objective

For a simulator that can respond to changing exposure and evolving vegetation, test a shared spatial model that predicts a next state from recent gas fields, an audited material state/history, static geometry, moisture, boundary conditions and the ignition forcing. Predict field increments and material changes with parameterizations that preserve useful training gradients. Total particle mass must not be mislabeled as remaining dry fuel.

Start with one-step prediction, then train progressively longer self-fed sequences and evaluate a complete 0–180-second autonomous history. A forecast initialized from true burning frames is a valid warm-start result, but cannot be presented as cold-start ignition prediction. A diagnostic supplied with true heat-release history must likewise be labeled an oracle.

This recommendation follows the modeling structure of the reacting-flow literature. It is not evidence that our current gas/material variables are sufficient or that a state model must outperform a direct space-time emulator. Retain the direct model as the controlled baseline. A physical-solver/learned-correction hybrid is a separate, larger engineering option if autonomous learned evolution proves unstable; it is not equivalent to the old bounded snapshot correction.

### Make physical success observable

Predeclare tolerances and report these separately, for ignition, active post-source burning and cooling:

- Gas-phase and solid-oxidation heat-release histories, peak magnitude/time and integrated energy; retain absolute errors when truth is near zero.
- Particle mass and temperature histories, with moisture loss and char/ash qualifications; a burnout definition based on declared heat-release/material criteria rather than disappearance of HOT gas alone.
- Continuous temperature error in hot regions and the whole volume, heat-release-density error in burning regions, plume extent and HOT precision/recall/F1.
- Velocity and radiation errors, plus autonomous rollout stability and temporal coherence.

Compare against constant/background, nearest-condition and, for state prediction, persistence baselines. Include conditional/replicate averages if that is the intended target, but do not substitute an averaged target without disclosure. Predicting the global source history separately is a useful diagnostic for distinguishing heat-production error from spatial-placement error; it is not a replacement for coupled evaluation.

### Use conventional selection and a genuinely untouched final test

Keep all seeds from one physical configuration in the same split. Evaluate train/validation every epoch, choose checkpoints using a declared validation criterion, and select a HOT threshold on validation if threshold tuning is part of the protocol. Then freeze the entire procedure before opening a new held-out evaluation. Existing examined cases cannot recover their pristine status by renaming them.

Measure a data-learning curve on nested subsets such as 32, 120 and 360 configurations with adequate optimization for each. Fixed update counts alone give the larger dataset fewer passes and confound the comparison. Training/validation curves and physical errors should decide whether the next investment is optimization, conditioning, data coverage or model capacity. Maximum epochs and wall-clock deadlines are budget controls, not convergence tests.

## What can be claimed now

There is evidence that spatial hot-region structure is predictable from the existing setup. There is not yet evidence of a faithful continuous ignition-to-burnout surrogate. The main demonstrated failures concern what was optimized, what was measured, and how incompletely the proposed dynamic approach was tested. The precise remaining balance between representation, optimization, missing state and data coverage is unresolved.

The reference simulations themselves use generic 3 m-wide conical crowns, 4/6/8/10 m tall above a 2 m base, 1,600 weighted particles, a 0.5 m grid in a 24×16×16 m domain and a 1500°C imposed ignition lasting about 20 seconds. They omit trunks, buildings and embers. Reproducing these FDS runs would be a useful bounded emulation result. It would not, by itself, validate realistic tree behavior or replace FDS outside the trained regime. These scope limits do not excuse failure to emulate the data already available.

The cumulative approved cap remains $125, with $109.10 in retained reservations and $15.90 unreserved at this review. Reservations are not an invoice. No additional paid work was performed for this review.
