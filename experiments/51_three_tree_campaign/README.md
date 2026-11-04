# Revised three-type campaign

User-authorized design: 2,000 unique one-tree cases, comprising667 pine-inspired,667 eucalyptus-inspired and666 coast-live-oak-inspired cases. Oak crown width is12 or14m and tree height10 or11m, all four combinations. No oak height controls. Pine/eucalyptus retain their25 size combinations each. Old experiments remain immutable.

`prepare.py` selects cases without ranking simulation outcomes. Twenty compact pine/eucalyptus results and two allowed-size oak results are reused by their original deck/proof hashes. The remaining1,978 require new simulations. Oak cases expand environmental/heating combinations within the four approved sizes rather than repeating identical simulations. Wind1–5m/s, moisture6–30%, loading0.7/1/1.3 and mutually exclusive base/crown heating remain in scope. Environment groups are assigned to train/validation/test before new simulations; historical pilots have already been inspected, so holdouts are not historically pristine.

Retain24×16m pine/eucalyptus domains,29×20m oak domains,0.5m cells and180s targets. Z is tree height+6m, with a16m minimum for oak. Generic vegetation and static woody thermal particles are not calibrated species chemistry; no protective bark, embers, grass or resolved solid trunk obstruction. The imposed heating patch is0.4×0.4m at1500°C for20s. Three-dimensional temperatures are saved every36simulated seconds;2D slices every2s. Compact-domain differences remain the previously accepted approximation, not proven equivalence.

## Remote adaptive checkpoint policy

The controller, not a local monitor, polls Batch task status and detects confirmed Spot preemptions via exit code50001 ([Google documentation](https://docs.cloud.google.com/batch/docs/troubleshooting#vm_preemption_50001)). It counts each task once even if an event is repeated; queued tasks do not dilute the denominator. Other failures are not evictions.

Start at480seconds of solver runtime between clean-stop requests. Within a wave, at least two confirmed evictions and a5% eviction rate reduces the interval to300seconds; at least four and a10% rate reduces it to180seconds. Reductions persist across waves, never increase automatically, and never exceed the original wall deadline. These are operational thresholds, not scientifically calibrated optima.

The workflow publishes immutable reduction markers in its unique cloud prefix. Running workers poll them every30seconds, including during a solver segment. If the shorter interval has already elapsed, the worker requests a clean stop promptly. Final state is still saved on exit. A clean stop may take up to900seconds, and upload adds further time: an8-minute request interval is not a guarantee of at most8minutes lost work. Forced stops do not produce accepted checkpoints. A control-read failure retains the last verified interval; it does not manufacture an eviction. Initial control access must pass before FDS startup.

`build_controller.py` generates the adaptation subworkflow and integrates it into the existing controller polling loop before terminal handling. `worker.py` consumes the same remote markers. Six mock-process/policy tests cover live changes, monotonic behavior, threshold boundaries and stop deadlines. No local FDS is run. This policy does not introduce automatic paid retries.

## Execution state

Offline design and deck preparation only. The controller template deliberately refuses submission until frozen inputs, scoped permissions, remote readiness, preservation and an admitted budget are supplied. It has not been deployed or exercised on actual evictions. `assess_admission.py` records the private affordability check; the conservative remaining simulation estimate plus training headroom fails current available capacity before additional storage/transfer allowances. Recent posted rates are lower, but neither future rates nor total runtime are guaranteed. No allowance is increased, no pending reserve is released, and no paid campaign has started.

## Bounded launch authorization

The user reiterated launch after the affordability warning. The new remote campaign is capped separately from protected training funds; it may stop before all2,000 cases. Six new canaries cover all four permitted oak sizes and one case each for pine/eucalyptus. Each later wave contains at most18 cases (72Spot CPUs). Workers retain2h solver/3h task limits; zero automatic retries. Before each wave the workflow checks its remaining compute allowance against a conservative maximum VM-time reservation. Completed wave wall time times task count is charged conservatively, including idle and cleanup time. This deliberately overestimates compute and may stop early; actual allocation reconciliation is required before reusing any remainder. Ancillary costs have a separate private reservation. This is not a guarantee that every planned case will fit.

Production workflow reads its private admission record remotely. Initial control publication and every wave run inside cleanup handling. No local monitor decides checkpoint intervals. A96h scoped read grant covers the72h campaign deadline. Actual cloud readiness and startup proofs, not mock tests alone, are required before claiming execution success.
