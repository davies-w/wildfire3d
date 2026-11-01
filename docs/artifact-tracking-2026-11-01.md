# Historical artifact tracking repair

The audit's uncovered regular files are now recorded at their original paths:
30,780 previously untracked files, plus 23 modified, uncached or stale-record
files corrected in this migration. Historical/source material uses 32 grouped
`historical-files.dvc` pointers. Existing pipeline outputs retain `dvc.yaml` and
updated `dvc.lock` records. All 260 original symlinks are recorded in Git.

The scoped upload verified 26,217 distinct DVC objects on Hugging Face, uploading
17,666 missing objects. Every remote size and Xet hash matched the source, and
new directory manifests passed anonymous MD5 readback. Uploads read original
files directly: no persistent DVC cache, local mirror or duplicate export tree.
The local verification record is
`experiments/43_repository_preservation/results/direct-hf/upload-verification.json`.

The audit exclusions are explicit: 113 financial/redaction-required records and
247 transient or tool-internal files. The complete local list is in
`experiments/43_repository_preservation/results/direct-hf/audit-adoption-plan.json`.
No spending ledger or private key was included. Fourteen original symlinks have
missing targets; Git preserves their text, not absent target data.

Two overlapping experiment 21 directory outputs were split into non-overlapping
outputs. With the user's explicit approval, six cyclic dependency links in
experiment 36 were removed and the 57 affected historical stages frozen. Their
original definitions and lock records remain in
[historical-dvc-dependencies.json](historical-dvc-dependencies.json).
`dvc dag` now succeeds. The frozen stages are historical snapshots, not a claim
that their original in-place workflows can be replayed from today's files.

The uploader's confidentiality and standard DVC directory-format tests pass.
A fresh-checkout restore test is pending; remote verification alone does not
establish that every old repository artifact or historical Git revision can be
restored. This repair covers the audited gaps, not a new audit of all old remote
objects.

See [storage.md](storage.md) for the repeatable metadata-only tracking and direct
HF upload commands. “DVC push” means that verified project script.
