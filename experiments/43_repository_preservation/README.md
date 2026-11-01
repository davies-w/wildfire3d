# Repository preservation audit

This audit covers locally present project source, reports, models, checkpoints,
training arrays, raw solver outputs and run metadata across the project. It does
not run a simulation, optimizer update or training job. Existing scientific
results are not revalidated by preservation.

The public DVC snapshot is `data/public`. `manifest.json` records each exported
path, byte size, MD5, SHA-256 and whether JSON metadata was sanitized. Model and
numerical artifact bytes are retained unchanged. Spending ledgers, financial
records and credentials are excluded. Financial or credential fields inside
otherwise useful JSON records are removed in the public copy. An archive that
contains excluded metadata is represented by its sanitized individual members;
its original package is retained locally, not uploaded as a whole.

Installed dependencies, caches, transient process files and prior duplicate
exports are not independent project artifacts and are omitted. Git-tracked
engine-area source is included. All originals remain in place. The snapshot is
an additional preservation record, not a replacement for experiment pipelines.

`audit.py` creates the inventory and sanitized snapshot. `track.py` adopts it in
an isolated DVC checkout, sharing the existing cache, to avoid the legacy
experiment21 overlapping-output graph. `push.py` uploads only this snapshot's
content-addressed graph to the public Hugging Face bucket and checks every
remote object's size and Xet hash, plus anonymous directory readback. It never
syncs the entire private mirror. `public-verification.json`, when present,
records successful verification; its absence means publication is incomplete.
