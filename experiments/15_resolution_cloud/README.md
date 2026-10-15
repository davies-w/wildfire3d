# Experiment 15: numerical cost, resolution sensitivity, and bounded cloud execution

## Aim

Identify which numerical choices could reduce the cost of future property-level FDS training data. Separate grid resolution, mesh-interface overhead, radiation work, conduction correctness, and vegetation mass conservation. This is a mechanism screening experiment, not a validated property ignition model.

## Local experiment and findings

All 18 runs completed their full requested physical horizon (609.7 seconds of total measured solver wall time), with four OpenMP threads and the native ARM executable. The synthetic flow and heated-wall cases use an 8 × 4 × 4 m domain and run for 8 simulated seconds. The prescribed propane burner heats an inert wall with wood-like thermal properties; the wall does not pyrolyze or ignite. Upstream FDS conduction and pine-needle decks check separate mechanisms. Source revision and input hashes are in `source-manifest.json`; per-run manifests record binary/deck hashes, load, elapsed time, outputs, and completion.

| Configuration | Cells | Heated-case elapsed time | Interpretation |
|---|---:|---:|---|
| Uniform 0.5 m | 1,024 | 3.09 s | Much cheaper, insufficient evidence of fidelity |
| Uniform 0.25 m | 8,192 | 10.70 s | Medium baseline |
| Uniform 0.125 m | 65,536 | 107.85 s | Numerical comparator, not ground truth |
| Three meshes, all 0.125 m | 65,536 | 141.13 s | Partition/interface overhead in this single-process setup |
| Central 0.125 m, outer 0.25 m | 36,864 | 90.82 s | 44% fewer cells yielded only 16% less elapsed time |
| Medium grid, cheaper radiation | 8,192 | 8.93 s | About 16% less elapsed time; fidelity is unresolved |

Refinement increases both cell count and the number of timesteps. The heated fine run took 786 steps versus 314 at medium resolution. Local refinement retained 764 steps: the fine cells still constrain the timestep. Splitting meshes alone did not accelerate these single-process runs. This does not evaluate distributed MPI scaling.

In the medium heated case, radiation accounted for 32.5% of reported routine time and combustion for 20.8%; pressure accounted for 3.6%. With cheaper radiation, its share fell to 15.5%. These are workload-specific measurements, not a prediction for a full property with embers, complex geometry, and reactive materials.

Surface-temperature differences versus the finest grid were substantial and non-monotonic. Even identical fine cell sizes with different mesh partitioning produced different transient solutions. The 8-second windows are too short for statistically converged turbulent averages; a lower difference from one comparator does not establish higher physical accuracy. No candidate is established as accurate within X%, and no ignition label is inferred from this study.

Raw boundary verification: `boundary_check.py` invokes the distributed `fds2ascii` on the fine heated case's west-facing wall at x=4 m. Over the 7–8 s averaging window, surface temperatures ranged from 39.819 to 501.5 °C. These spatial/time-averaged boundary values are distinct from instantaneous device maxima. Raw extraction and metadata are retained under `data/boundary/` and `results/boundary_check.json`.

The slab conduction check differed from the analytical solution by at most 0.821 °C across six depths and 100–2000 s. The closed hot pine-needle box conserved initial solid plus evolved water and fuel mass within 0.000540 kg (0.054% of initial mass). The latter tests drying/pyrolysis and conservation, not flame spread or real vegetation ignition.

Other applications were consuming CPU during these runs. Repeated medium-case elapsed times ranged 6.45–7.16 s for flow and 10.09–10.70 s for heating. Inputs and completion were controlled; laptop scheduling was not. Treat small timing differences cautiously. Full measurements appear in `results/findings.md`, `results/local_analysis.json`, and `results/profiling.png`.

## Cloud trial and cost controls

Dedicated project: `tmrw-wildfire-20261015`, billed to the user-approved Project TMRW Mercury Billing account. The existing USD10 cumulative budget provides alerts only. The initial cloud trial has a separate USD0.50 total allowance, including build and overhead; it is not a provider-enforced dollar cap.

Prepared controls: one Spot c3-standard-4 worker at a time, no on-demand fallback, no retries, bounded task duration, a separate server-side workflow deadline and cleanup, fixed job ID, immutable image digest, 25 MiB output cap, 30 GB boot disk, and one-day bucket/image expiration. The launcher reserves costs before submission and admits at most three trial jobs. It refuses active prior workflows/jobs/workers and stops admitting work above USD0.40. Owner API calls can bypass this local launcher.

Planned conservative reservations: USD0.12 for a maximum 20-minute image build, USD0.075 for three workers at 15 minutes each using a USD0.10/hour allowance, and USD0.10 for storage/network/control overhead: USD0.295 total. These are estimates, not settled billing charges. No repeated paid builds or job retries are authorized automatically.

The three intended probes are a successful science job, a deliberate task timeout, and a deliberate independent-workflow deadline cleanup. All require evidence of final state and zero remaining workers. The cloud compiler/OS/architecture differ from the laptop even at the same FDS revision, so scientific outputs must be compared alongside timing.

Current deployment state is recorded in `results/cloud-deployment.json`. Workflow/job files containing an all-a placeholder digest are templates and must not be deployed. No cloud result is claimed until execution evidence is recorded.

## Reproduction

From this directory, `../../.venv/bin/dvc repro` runs the local pipeline. Use `dvc pull` to retrieve cached data where available. `dvc commit -f` adopts the existing runs without solving them again. Python dependencies are numpy, scipy, matplotlib, and PyYAML, plus the native FDS executable and distributed fds2ascii identified by the scripts.

Cloud actions are deliberately excluded from automatic DVC reproduction so it cannot create paid resources. After approved IAM, one bounded image build, and deployment validation, regenerate workflows with `make_workflow.py --image IMAGE@sha256:DIGEST`, record the verified deployment, and invoke `launch_cloud.py science`, then `timeout`, then `watchdog`, checking results and cleanup between each. Do not mark a deployment verified merely because a file was generated.

## Next scientific step

Extend the promising configurations to longer transients and repeat realizations, then test reactive wall/material models across multiple heating regimes. Measure ignition classification and time-to-ignition sensitivity directly. Only after those checks should any speedup be used to generate property-risk training labels. This experiment does not address the previously reported GEOM/ember crash.

The two upstream input decks are preserved byte-for-byte, including their original whitespace. Git whitespace checks consequently report inherited whitespace in those files and their generated deck copies.
