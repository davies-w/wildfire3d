# Experiment35 attempt06: baseline audit and coordinate/time representation

First quantify the exact equal-channel standardized encoded MAE of ambient/zero-HRR/meanwind/zero-transverse-velocity baselines on the original eight TRAIN configurations, per channel and ignition/post-source/late windows. Radiation alternatives: zero, or each case's initial-frame spatial median held constant. No optimizer is used for the audit. Local raw archives and decks are SHAverified. Keep the decoded single trajectory as a DVC output.

Audit already finds that x32_033_s0 post-source hot-temperature occupancy is0.1371%, HRR>0.01kW/m3 occupancy0.2588%. Ambient with initialmedianradiation scores0.11042 post-source; HRR contributes0.01106/6=0.001844 to that mean. Fullhistory baseline0.14214. This quantifies weak objective cost of ignoring sparse burning, not proof of sole causal explanation.

Next test an explicit x,y,z,time coordinate MLP: six fixed dyadic Fourier frequencies per coordinate, three128wide SiLU hidden layers, six raw encoded outputs. No spatial coarse-grid decoder, no HRR trainingclamp. Physical decoding still enforces bounds. Same channel scales and unweightedMAE; no auxiliary losses. This can memorize one simulated burn; no claim of a general fire simulator.

Prespecify9withheld timeframes indices5,15,...85;82otherframes train. Every training cell-time sample visited once each epoch, uniformly shuffled, batch16384.40full epochs, AdamWcosine1e-3→1e-5,weightdecay1e-5,gradientclip5. All91fullfields evaluated everyepoch, separated into training and withheld-time interpolation. Heldout frames are within the same realization, not an independent trajectory or pristine test. This tests fitting and temporal interpolation, not transfer to another crown. Record allchannel physical/encoded errors, hotT>50C region, HRR>0.01kW/m3 region, totalHRR timehistory, ignition/postsource/late windows. Initial/each-epoch checkpoints uploaded; every250steps preserve optimizer,scheduler,RNG,scheduleposition,partialloss. CUDArestore exactforward replay required. Training GPUonly.

One fully reserved4.50USD cloud attempt would take cumulative97.10/100 including all retainedfailures/archive, invoiceunknown. Reserve BEFOREupload/compute. Expected20–45minutes afterallocation;20minqueue90mintask95minVM120minabsolute. No automatic retries or unreserved extension. Single lockedcollector verifies noVM/job/disks and removes exact24hinputgrant. Package contains SHAverified decodedtrajectory, avoiding oldGCSexpiry. Preserve allcode/workflowgenerator/Git andDVC/publicHFarchive.

Generic3mwideconicalcrowns4/6/8/10mabove2m,1600weightedparticles,.5m24x16x16m180s,artificial1500C20ssource,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature. Snapshotcoordinate/time representation, no recurrence or evolvingfuelstate; no physicalvalidation. No newFDS.

Heldout-time caveat: normalization is deliberately frozen from the prior eight-training-case audit, which included these frames. They are withheld from current gradient updates, not from historical scale estimation. This is an interpolation diagnostic, not a clean independent validation estimate.


## Completed coordinate diagnostic (attempt06)

All 40 complete epochs finished: 4,030,464 cell-times per epoch, 246 updates per epoch, 40,582 parameters. CUDA checkpoint replay passed. All 91 frames were evaluated every epoch. Cloud VM, job and disks are absent and the exact temporary input grant was removed.

Matched all-frame post-source comparison (same times and cells): constant ambient/zero-HRR/mean-wind/initial-median-radiation baseline objective 0.110424; coordinate model 0.062210 (43.7% lower). Whole-volume temperature MAE was only 0.1785 C, while hot-region temperature MAE was 61.36 C (baseline 88.91 C). Burning-region HRR MAE was 12.477 kW/m3 versus baseline 12.552, and total-HRR relative L1 error remained 99.43%. Thus the large average-loss improvement did not reconstruct burning faithfully. HRR encoded-channel error was 0.012073 versus baseline 0.011063: worse under that exact channel objective. Only 0.1371% of post-source cells were hotter than 50 C and 0.2588% exceeded 0.01 kW/m3 HRR.

Final full-history objective: training 0.073417, withheld-time 0.077299. From epoch35 to40 these improved by only 0.26% and 0.09%, respectively, under a cosine schedule ending at 1e-5. This establishes flattening under this schedule, not a representation-capacity limit or sufficient optimization under every schedule. Neither reached the earlier 0.05 normalized fitting target, which itself is not a physical-fidelity criterion. Late-time HRR percentage errors have near-zero truth denominators; use the retained absolute errors rather than those percentages as a fidelity measure.

Decision: the requested diagnostic is complete, but the prerequisite successful single-trajectory burning fit has NOT been achieved. Do not expand data or resume auxiliary-loss sweeps on this evidence. No general burning surrogate or state-to-state model has been established. Any next experiment needs a separately specified hypothesis; current results do not prove that adding evolving material state will work.

The nine withheld times are interpolation in the same realization, and historical normalization includes those frames. This is not independent validation. The underlying simulation uses generic 3m-wide conical crowns, 1600 weighted particles, a 0.5m mesh in a 24x16x16m domain and an artificial 1500 C ignition source for20s; no trunks, buildings or embers. Outputs are six gas fields, not solid-ground temperature. The coordinate model has no evolving fuel state or recurrence. Projection images show maximum-through-y gas temperature/HRR, not flame geometry.

All failures and archival allowances remain reserved: cumulative $97.10 of $100, with $2.90 unreserved. Invoice cost is unknown. No further paid job launched.
