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

The independent [coverage check](artifact-coverage-verification.json) accounts
for all 31,401 original audit candidates: 30,780 exact DVC matches, 261 exact Git
matches, and the 360 explicit exclusions above. No candidate is unaccounted for.
The [upload receipt](artifact-upload-verification.json) records remote verification.
The uploader's confidentiality and standard DVC directory-format tests pass.
The [fresh-checkout restore test](artifact-restore-verification.json) passed:
31,698 files across 99 targets were restored from HF objects and independently
MD5 checked. Git metadata came from GitHub commit `87c79e8`. HF batch download
was followed by standard DVC checkout using isolated exact output records.
Plain HTTP `dvc pull` hit HF resolver rate limits, and whole-stage checkout
included uncached sibling status outputs and raised `StorageKeyError`; neither
is claimed to have passed. The scoped restore mechanism avoids those problems.
The disposable test checkout and cache were removed afterward.

This repair covers the audited gaps and their scoped pipeline objects. It does
not establish preservation of every earlier Git/DVC revision, absent external
symlink target, or excluded private record.

See [storage.md](storage.md) for the repeatable metadata-only tracking and direct
HF upload commands. “DVC push” means that verified project script.
