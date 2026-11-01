# Repository preservation audit

This audit covers locally present project source, reports, models, checkpoints,
training arrays, raw solver outputs and run metadata across the project. It does
not run a simulation, optimizer update or training job. Existing scientific
results are not revalidated by preservation.

The public DVC snapshot is `data/public`. `manifest.json` records each exported
path, byte size, MD5, SHA-256 and whether JSON metadata was sanitized. Model and
numerical artifact bytes are retained unchanged. Spending ledgers, financial
records and credentials are excluded. Financial or credential fields inside
otherwise useful JSON records are removed in the public copy. An archive containing excluded metadata is repacked with that metadata removed;
scientific member bytes remain unchanged. The public container therefore has a
new digest, recorded in the snapshot manifest, and does not match its original
cloud package digest. The original package remains local. Scientific runtime
flags such as `stopped_by_budget` are retained; they are not spending ledgers.

Installed dependencies, caches, transient process files and prior duplicate
exports are not independent project artifacts and are omitted. Distinct older
model or numerical dataset versions are retained under `historical-model-archive`. Git-tracked
engine-area source, local case outputs under `FDS/cases`, ad-hoc `FDS/runs`,
and the custom no-front helper are included. All originals remain in place. The snapshot is
an additional preservation record, not a replacement for experiment pipelines.

`audit.py` creates the inventory and sanitized snapshot. `track.py` adopts it in
an isolated DVC checkout, sharing the existing cache, to avoid the legacy
experiment21 overlapping-output graph. `push.py` uploads only this snapshot's
content-addressed graph to the public Hugging Face bucket and checks every
remote object's size and Xet hash, plus anonymous directory readback. It never
syncs the entire private mirror. `public-verification.json`, when present,
records successful verification; its absence means publication is incomplete.

The separate `private` DVC stage retains excluded original spending records and
unredacted legacy metadata in the local mirror only. The public uploader is
explicitly limited to the `snapshot` stage; it cannot select the private stage.
Previously committed ledgers remain in older Git history: removing current
tracking prevents future updates but does not rewrite published history.

DVC control files named `.dvcignore` cannot occur literally inside a DVC output.
The snapshot preserves their bytes as `.dvcignore.preserved`; each manifest row
records the original `source` name for restoration. Original Git files are unchanged.
Scientific file-hash references are retained even when names contain words such
as `energy_budget`; this does not expose the referenced file's private contents.

Verified publication: the snapshot contains 157,680 files including its manifest,
with 132,145 content-addressed objects. Every remote object passed size and Xet
hash verification, and the directory passed anonymous readback on
2026-10-31 (America/Los_Angeles). See `public-verification.json`. Local MD5 and
SHA-256 checks also passed. The private local mirror was independently checked
for all 833 objects representing 943 files.
