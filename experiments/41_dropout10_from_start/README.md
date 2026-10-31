# Experiment 41: dropout from the start, rotation 0

Fresh seed3516 weights and empty AdamW, with 10% dropout after the shared64 SiLU feeding both the four-delta and three-gate heads from epoch1. Evaluation disables dropout. No parent weights or completed epochs are inherited. The GRU has64 recurrent units; the shared dense64 layer adds no recurrent memory.25159 parameters, eight four-state samples and nine external features.

Frozen rotation0:1662 training,210 validation,208 test histories /204 test configurations. Same integral objective plus gate BCE0.1, AdamW3e-4, weight decay1e-4, gradient clip1, batch256. Windows:1 at epoch1,8 at21,16 at41,32 at61,64 at110,full90 at130. Minimum160, maximum400, patience30; validation selection is frozen before test evaluation. Full90 uses one origin/history and7 updates/epoch versus176 at64; epoch counts do not represent equal optimization exposure. This historically examined dataset is exploratory, not pristine confirmation that dropout generalizes.

Three ownership-gated Spot T4 queues race in Oregon, Iowa and South Carolina. One cloud controller removes losers and verifies empty resources before granting training ownership. No allocation deadline;12.5h training soft limit,12.75h task limit,13h VM limit. Runtime is uncertain; cloud loss/backward timing is advisory. Every completed epoch saves model, optimizer, RNG, history and selection. Evictions lose only an unfinished epoch; any continuation needs verified checkpoints and remaining authorized allowance. No local training.

Cloud startup verifies actual losses at all six horizons, nonempty optimizer/RNG next-update replay, and exact fresh epoch1 first-batch replay with dropout active. Probe weights are discarded. The actual completed epoch1 separately verifies serialized evaluation, optimizer presence and RNG restoration. No performance result yet.

Source and DVC pointers are committed/pushed. Scientific inputs and progress use scoped public Hugging Face artifact export; budgets and private control-plane evidence remain private. Never rerun launch after submission intent; inspect cloud state first.

Submitted once on 2026-10-31 at14:38:03UTC: `fds-gpu41-pool01`, execution `174000c2-5461-4730-9211-9c0835126de1`. Do not resubmit. Use `monitor.py`; fetch verified completed epoch scores using `fetch_progress.py or|ia|sc`, then `snapshot_progress.py`. The curve contains only this fresh run. Run `preserve.py` and `track_artifacts.py`, followed by scoped `push_artifacts.py --stage prepare|progress|collect`; private provenance stays mirror-only.

Completed284 epochs, selected254 by validation patience. All284 full checkpoints and208 test histories/204 configurations verified with SHA/MD5/generations and selection-before-test barrier. Selected validation4.972466%; final epoch train5.893380%, validation10.120930%. Test whole-sequence integrals: water6.284685%, dry fuel9.741815%, gas2.113929%, heating1.929901%. Compared with experiment39/40 selected parent, water/fuel/gas are worse and heating slightly better: no uniform generalization improvement.

All candidate jobs, VMs and disks are empty, exact read grant removed, and reservations closed after audited runtime accounting. The first pool completed without training restart. Scoped public artifacts exclude private financial evidence.

Published report: https://wdavies-fire-reports.static.hf.space/dropout41/index.html . Added root index card, full-sequence scorecard columns and70-page gallery without changing previous cells/pages. HF publication commit `fb778a08280a49a1e280057dd03311f564493f9c`; exact repository readback and normalized live page verified. Report layout and gallery first/last/toggle verified.
