# Continuous raw-data-to-training pipeline

User authorized bulk generation of both agreed formats on2026-11-08, with per-scenario local raw deletion only after raw and training artifacts are DVC/HF verified. Training data stays local. No simulations, model training, or fitting/physics changes are authorized.

continuous_training.py --forever processes completed Experiment51 cases alongside the separate raw-archive uploader. It uses an exclusive worker lock, isolated HF plans and restoration directories, and no global uploader plan. Existing22case previews are reused rather than refitted. Other cases use the same11state anchored and14state free cones, original four-channel bookkeeping, source samples, interpolation masks/brackets and thresholds. Bulk conversion does not generate thousands of additional animations.

For each case:
1. Read the existing frozen completed-output DVC manifest from HF and verify its directory MD5. Restore every file in that case from HF, check all DVC hashes and original completion-proof SHA256 values. Missing/unverified sources defer conversion and retain raw data.
2. Generate both formats, preserving exact observed samples, or reuse validated preview bytes after checking the source temperature hash. Validate finite values, times, shared four channels, unit directions, exact observed rows, interpolation bounds and first-transition examples.
3. Adopt the individual training-case output into a frozen DVC stage. Upload through scripts/dvc_hf.py with isolated reviewed object plan; verify remote hashes and independently restore the whole training-case directory. Retain training data locally.
4. Commit/push DVC metadata and confirm the commit is on the remote branch.
5. Only then preflight and unlink exact local solve files whose current hashes match the existing raw DVC manifest. Unknown or changed files block deletion. Keep completion proofs and original DVC locks. Remove this worker's verified temporary raw restoration; retain training restorations. No cloud deletion and no deletion of interrupted/unaccepted cases.

The1899verified simulation count is not a training conversion count. Initially1877cases have per-case proof paths;22earlier reused cases need separate source mapping. A per-case defer receipt records failures; no case is silently accepted, relabelled or replaced. The monitor must resolve deferred cases and the remaining source mapping before declaring completion. Existing older raw staging copies need explicit exact-hash reconciliation; the per-case deletion receipt lists exactly what was removed.

This pipeline processes Experiment51's agreed dataset schema. The standing all-experiment raw backup/audit continues separately; incompatible experiments are not silently forced into this schema. The four-state and sparse hot-gas geometry limitations remain as documented in CONE_COMPARISON_PREVIEW.md. Interpolation cannot recover unsaved early motion or peaks, and a free-cone tip is not necessarily a physical combustion origin.

Reused cases use `--reused-only`: original Experiment49/50 DVC manifests, proof hashes, source filenames and original expected class masses are checked explicitly. Target Experiment51 identities and source identities are both retained. No fitting or physical definitions change. The ordinary worker must be stopped at an idle boundary before this queue runs, so there is one shared DVC writer.
