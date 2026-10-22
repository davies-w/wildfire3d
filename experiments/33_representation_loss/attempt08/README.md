# Attempt08: matched loss/evaluation comparison

Three identical GeometryCNN copies start from current6000 weights AND optimizer, use schedule seed3308 and2500additional updates. Control: targeted encoded loss. Dose: replace encoded radiation term by0.1 times three-frame positive-radiation-excess absolute error normalized by reference mean+1. Dose_background: also increase encoded cold-temperature weight0.1→0.5. This isolates the dose replacement and then background penalty; neither is full-history optimization or recurrence. Initial evaluation occurs after restore and weight hashes must match. Evaluate all20full histories with unchanged physical/percentage metrics, including weak fires and background. A successful direction must improve radiation without sacrificing temperature/heat substantially; report all tradeoffs, not just training loss.

Pilot07 found revised-model radiation-dose candidate norm3.15 versus bright encoded0.407; adding it at unit weight is not justified. Gradient cosine is local diagnostic evidence, not causal proof. Here0.1 is fixed before validation and not tuned on test data.12train/8validation are deliberately strength-stratified development cases, not IID/pristine test; old exp32 tests remain examined.

No new FDS. Generic3m-wide conical crowns4/6/8/10m above2m base,1600weightedparticles,.5m grid24x16x16m,180s,1500C artificial20s source,no trunks/buildings/embers. Six gas fields, not solid-ground temperature; no physical validation.

Reserve$2 full allowance before submission, cumulative cap75. Regular L4 us-central1-c. Expected10–20minutes; cloud20minqueue/60mintask/65minVM/90minabsolute deadlines. Checkpoint every500updates; separately budgeted replacement required after interruption, with new prefix. No laptop training. DVC submission/collection stages execute the workflow and retain outputs.

## Measured outcome

All3initial weights and full-history metrics were exactly identical. Post-source median validation errors (hot temperature / HRR curve / radiation dose / whole-volume temperature rise), percent: control50.05/69.45/126.83/798.38; dose49.78/65.62/67.71/1065.99; dose_background50.06/67.24/66.91/412.73. Dose_background reduced radiation and whole-volume temperature errors in all8validation configurations versus matched control. Training errors likewise improved for radiation90.72→47.80 and wholevolume461.74→245.38. Hottemperature42.89→42.91 and HRR22.52→24.54 show the tradeoff. This supports the short-window physical-dose loss and stronger background weight on this development sample, not general validation.

Weakest validation case x32_388_s0 averages1.314kW truth after source: wholevolume MAE4.61→2.19C and radiation relativeerror9014.6→1045.5%. Thus relative errors remain huge when truth is small; this is not solved. All-arm median minimum6C reaches the model floor; insufficient metrics to localize or quantify cold pockets. Follow-up09 tests physical-unit background-temperature penalty from identical initial states, with fixed coefficients0.02/0.1, not more data. No additional FDS.

Report hash verified, VM/job/disks empty and temporary input permission removed. All checkpoints retained. DVC analysis records all/after-source/late metrics, per-configuration differences and weak cases. Cumulative reservations46.60USD; actual invoice cost unknown.


Reproducibility follow-up:09 repeated this dose_background control with identical initial predictions, but final wholevolume temperature error changed412.73→568.99%. An initially suspected optimizer alias is NOT established: although initial load shares tensors, the existing serialization/restore before training breaks that sharing. Full-path no-training check in09 confirms isolation. Deterministic repeat in10 will test reproducibility. Treat small differences cautiously.
