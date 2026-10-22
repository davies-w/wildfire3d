# Existing-run diagnosis and proposed follow-up

No new FDS simulations or cloud jobs were launched. diagnose.py reads existing device/HRR CSVs and extracts raw west-wall boundary fields with fds2ascii; results/diagnosis.json retains measurements, windows and patch locations. Surface: x=14, y=10..14, z=0..4, first mesh, IOR=-1. Boundary flux numbers below are maxima over patches of each patch's 0–10 s mean, in kW/m², not instantaneous peaks or absorbed surface flux.

## Findings

At equal 1700 kW total source strength, A+C ignites at 13.03 s while A+D never ignites by 90 s. Both contain the near-wall crown A=(12,12). C=(10,14) is offset sideways; D=(8,12) is directly upwind of A. Structure west face is x=14. Wind is toward increasing x.

Before either house ignites, A+C's hottest west-wall patch receives a 0–10 s average gauge exposure of 6.52 kW/m²; A+D receives 2.16. At 10 s, total HRR is approximately 3777 versus 5395 kW, respectively. Particle mass lost from 1 to 10 s is approximately 0.37 versus 0.82 kg. More total combustion/mass loss therefore does not ensure more heat reaches the structure. Particle mass loss includes drying and pyrolysis and cannot be equated directly with combustion energy.

A+D at 1700 kW peaks at 347.9 C at 20.5 s, only 2.1 C below the prescribed 350 C ignition rule. At 3200 kW it peaks earlier, at 11.5 s, at 339.6 C. Its particle mass falls faster with the larger source. This is consistent with changed heat-release timing and heat delivery, not a monotonic source-power-to-wall-temperature relationship. It does not prove an exact fluid mechanism.

The ignition burners ramp down from 30 to 31 s. In non-igniting A+D cases, total HRR at 40 s is only 18.7 kW (1700 source) or 12.0 kW (3200 source), and is near zero by 60 s. West-wall mean exposure in 32–60 s peaks at only 0.34/0.33 kW/m². The existing vegetation/source combination does not maintain a substantial fire after that ignition exposure. Post-ignition HRR in A+C/AB cannot be attributed to vegetation because the burning house adds fuel.

Distant one-crown cases are different from this near miss: B and C have centers 4 m upwind of the wall and offset 2 m laterally; D is 6 m upwind. Even at 3200 kW source power, their maximum house temperatures are 278.5, 270.2 and 109.3 C. Moving some fuel closer is a more targeted way to seek positive examples than endlessly increasing an upstream burner.

## What remains unidentifiable

Velocity slices, separate wall convective/radiative flux histories and per-crown mass histories were not saved. We cannot uniquely distinguish plume deflection, shielding, drag, and altered local flame duration. The current data also lacks burner-only controls, so it has not established whether successful house ignitions require vegetation. This should be resolved before scaling DNN data production.

## Proposed action

First run five diagnostic controls: A+C burners only; A+D burners only; A+D with the upstream crown removed but both burners retained; and two fresh-seed repeats of A+D at 1700 kW to assess the near-threshold sensitivity. Retain both outcomes rather than selecting lucky igniting seeds.

Then, subject to those controls, test three two-crown arrangements at 1700 kW total: retain A=(12,12) and put the second crown at (8,10), (11,14), or (12,10). These respectively test moving the upstream crown out of line, moving offset vegetation closer, and placing both crowns near the wall. Compare full-power exposure through 10 s versus the existing 30 s, each followed by a 1 s ramp down. This adds six cases. Shorter exposure tests dependence on the prolonged burner; it is not assumed to create more positive cases. Do not lower the house ignition threshold or alter its material to manufacture positives.

Add per-crown mass diagnostics, wall RADIATIVE HEAT FLUX / CONVECTIVE HEAT FLUX / TOTAL HEAT FLUX, and sparse airflow/temperature slices. These quantity names are supported by the pinned FDS source (Source/data.f90). Only after checking the controls should a broader set of varied positive and negative examples be generated. Proposed geometry changes are hypotheses, not guarantees of ignition.

Maximum 11 new simulations. Estimated incremental Google Cloud total $0.20–$0.24 with a $0.25 allowance, one existing-image c3-standard-4 Spot worker, no retries, and a two-hour controller deadline. At $0.065744/hour, two hours compute plus the full $0.10 ancillary allowance is $0.2315. This is an estimate, not a guaranteed billing cap. The detailed case list is results/diagnostic-followup-plan.json. Nothing in this proposal has been launched.
