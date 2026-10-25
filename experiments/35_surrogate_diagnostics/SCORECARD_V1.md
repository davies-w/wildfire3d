# Frozen evaluation scorecard v1

The user froze this approach on October24,2026. The normative machine-readable specification is scorecard-v1.json, with SHA256 references to the evaluated implementations. This freezes evaluation, not model features or a new training run.

Use16seconds as the headline forecast, with2/8/16/32/90second horizons and a separate full180second autonomous rollout. Predictions feed back after observed history. Compare each forecast with its own simulation and a baseline that holds the starting state constant.

Activity is simulation-defined and identical for every model. In a trailing nominal10second window, substantial activity is at least0.1% of initial dry-fuel-equivalent release or water loss per10seconds. Quiet means both below0.01%; keep weaker residual changes separate. Fuel-gas release is converted with the existing0.75yield; it is not actual combustion heat. Drying is separate from release. The stable activity/quiet/residual forecast groups require every step to qualify; remaining windows are category transitions, not necessarily ignition or extinction. These are engineering thresholds with smoothing lag, not physical validation.

Show two separately labelled tables: error vs simulation (lower is better), and error reduction vs no change (higher is better). Always include absolute errors and denominators, especially for near-zero gas release. Aggregate per history, then seed replicas/configurations, then folds; preserve identical eligible samples. Never average per-case percentage errors as the headline. Include every output a model predicts; mark absent outputs “not predicted” and untrained variants “not trained.”

Report total released amount, peak, cumulative release timing, water/fuel net loss, quiet drift and physical invalidity alongside pointwise errors. Best time-shift alignment is only an optimistic diagnostic. Add median/90th-percentile configuration errors and the fraction beating no-change, with ties and counts explicit.

Coverage must be honest: current v1 activity tables cover16seconds only. Other horizon tables still use older broad masks. Scenario-distribution and water/fuel net-loss summaries are specified but not yet implemented in the current report. No four-state MLP exists. Historically examined and reshuffled folds are not a pristine benchmark.

Model selection and stopping use a predeclared validation criterion; tests cannot select thresholds or checkpoints. Any scorecard change requires a new version, a stated rationale and side-by-side v1 results. Retain this file and specification unchanged.

Current prioritization: quiet/end-of-activity drift is a demonstrated failure. The previous spatial addition was three vegetation surface-heating location moments, not a burning/plume/heat-flow vector, and worsened original-state prediction. Studying cessation is a justified next proposal, not an authorized training launch. Do not impose automatic zero gas or freezing at20seconds: different histories stop at different times, and water/fuel need not be depleted.
