# Reduced domains and selective resolution with particle vegetation

Aim: measure whether reducing the surrounding CFD volume and coarsening its outer regions saves aggregate CPU time while preserving structure ignition near the model's ignition threshold.

Status: complete. All 17 FDS runs reached the full 90-second horizon. Cloud cleanup succeeded; final inventory was zero VMs, disks, and Batch jobs. The raw boundary extraction, analysis, plots, and DVC reproduction completed locally.

## Findings

The full-domain 0.5 m reference used 55,296 cells and about 10.7–11.0 aggregate CPU-minutes per 90-second scenario. The full-domain source-strength bracket was 387.5 kW/m² per 1 m² burner with no structure ignition and 459.375 kW/m² per burner with ignition at 25.01 s. Its 15.65% relative width missed the planned 10% target. At the lower endpoint, the mixed-resolution case ignited at 28.03 s while the full-domain reference did not; raw six-face burning-rate data confirms that label change.

| Variant | Cells | Mean CPU speedup | CPU min per endpoint | Ignition labels matched |
|---|---:|---:|---:|---:|
| Mixed resolution, full domain | 11,280 | 2.60× | 4.23, 4.13 | 1/2 |
| Tight reduced domain | 15,360 | 2.13× | 4.79, 5.41 | 2/2 |
| Tight domain with coarse exterior | 12,672 | 2.37× | 4.31, 4.85 | 2/2 |
| Wide reduced domain | 27,648 | 1.68× | 6.26, 6.64 | 2/2 |

The best reduction was 2.67× CPU for the mixed-resolution high-source case. The tight and combined variants matched the binary labels at these two source strengths, but their pre-ignition maximum wall-temperature differences reached 149 °C and 225 °C, respectively. The wide variant stayed closest to the full reference at the non-igniting endpoint (3.71 °C maximum temperature difference), but differed by up to 97.66 °C at the igniting endpoint. These comparisons do not establish a generally accurate reduced model or a 10× path. The best observed CPU cost is near five minutes for this limited 90-second synthetic scenario; some candidate cases remain above five minutes.

Foliage and three branch-size classes were modeled as stationary FDS vegetation particles using the 14%-moisture Douglas-fir validation example's fuel properties, not as solid-block trees. This is not an eucalyptus model. The geometry is a synthetic 6×4×4 m combustible structure with a prescribed 350 °C ignition criterion, two conical crowns, and two controlled 1 m² ignition burners. The horizon is 90 seconds; a negative label means no ignition within that interval. No embers were included, and the full-domain 0.5 m mesh is a comparison reference, not a demonstrated mesh-converged truth.

The rate-based estimate from the completed 69.4-minute workflow is about $0.076 for Spot compute. Adding the full $0.10 ancillary-charge allowance gives an estimated total of $0.176 before credits. The $0.40 allowance was a conservative stop budget, not a billing cap; the posted invoice is not yet confirmed. No image build was needed.

## Fixed physical scene

A synthetic 6 x 4 x 4 m combustible structure, two 2 m conical Douglas-fir particle crowns (one off-axis), 3 m/s wind, and two 1 m² ground ignition burners operating for 30 seconds. Both crowns use stationary weighted particles for foliage and three branch-size classes; there are **no solid-block trees**. Chemistry, thermal properties, 14% moisture, dry mass density and crown dimensions come from the pinned FDS NIST_Douglas_Firs validation input copied into inputs/. These are dry Douglas-fir benchmark parameters, not live eucalyptus properties. The structure retains a synthetic 350 C ignition criterion and prescribed burning after ignition. No ember transport is included.

The core x=8..22, y=8..16, z=0..6 is always 0.5 m, is the first mesh, and contains every fuel element, burner and the complete structure. All six mesh regions are adjacent and non-overlapping. The same physical geometry, ignition powers, fuel parameters, seed, timestep controls and output intervals are used in comparisons. Outer coarse slabs use 2, 1 or 0.5 m cells as needed to keep at least four cells per dimension. Startup and T_END=0 CHECK_MESH_ALIGNMENT checks passed locally for all variants.

| Variant | Domain x,y,z (m) | Cells |
|---|---|---:|
| full | 0..24, 0..24, 0..12 | 55,296 |
| wide | 0..24, 6..18, 0..12 | 27,648 |
| tight | 4..24, 6..18, 0..8 | 15,360 |
| mixed | full domain, coarse exterior | 11,280 |
| combined | tight domain, coarse exterior | 12,672 |

The combined case has more cells than mixed because thin outer slabs require finer cells for the pressure solver. This is an actual implementation constraint, not a typo. Cell ratios are not measured speedups.

## Near-threshold design

All cases run the same 90 simulated seconds. Full-domain source strengths initially bracket 100 and 2400 kW/m² per burner, with an optional zero or 4800 endpoint if required. Up to five bisections seek an ignition/non-ignition pair within 10% relative source strength. If the bracket remains wider, its measured width is reported; near-threshold coverage is not assumed. Both bracket endpoints are compared in mixed, tight, combined and wide variants, then repeated at another random seed if budget permits. A solver failure or incomplete horizon cannot count as non-ignition. The threshold concerns this 90-second exposure only.

CPU time comes from process wait4 user+system usage, not four times elapsed time. Full horizon rather than early ignition stopping keeps runtime comparisons consistent. Compare ignition label/time, pre-ignition temperature and heat-flux histories, fuel mass initialization, and raw boundary temperature/burning rate. Device comparisons end before either member ignites, avoiding contamination by the newly burning house. Full reference mesh convergence is not established by this study.

## Cloud spend and controls

Pre-run estimate was $0.20–$0.30 total with a conservative $0.40 allowance. The run reused the existing pinned container; it used one c3-standard-4 Spot VM, with no retries or on-demand fallback. Campaign allowance was 9,900 s, Batch task maximum 10,380 s, and independent cleanup controller maximum 10,800 s. At the listed $0.065744/hour Spot rate, the three-hour compute ceiling is $0.197232, plus $0.10 ancillary allowance. Estimates are not an invoice or a guaranteed dollar cap. Existing project-scoped watchdog permissions were reused without new IAM grants.

`cloud.py launch` is explicit, single-use and never part of `dvc repro`. `fetch.py` only downloads outputs. `evidence.py bundle` creates the external evidence input; DVC restoration and analysis do not launch paid compute. Raw simulation outputs live under data/, never Git. No restart files are retained.
