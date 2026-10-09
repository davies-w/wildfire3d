# 10 — Validating the hand-built arm64 FDS

**Question.** The native arm64 build was made from source on this machine. Is it
correct, or merely fast? Does it produce the same physics as the stock binary?

**Why this needs an experiment at all.** HYPRE and SUNDIALS were **not found
during the build and are not linked in**. That is a real reason to suspect the
build, so it was checked rather than assumed.

**Method.** The same case (`wtest.fds`) solved single-threaded under both
binaries, comparing heat release rate step by step.

**Result.**

- Agreement to **1e-6 – 1e-4** over the first 5 s
- Divergence growing **exponentially**, reaching ~2% by t = 15–29 s

**Conclusion — this is the correct behaviour, and the build is sound.** Fire
simulation is Large-Eddy Simulation, which is chaotic. Two runs of the *same
binary* at different thread counts diverge the same way. Trajectories separate
exponentially; that is a property of the system, not a bug in the build. The
test that matters is the first seconds, where agreement is at round-off.

An earlier scare — time stamps in the `.bf.bnd` file appearing not to cover the
end of a run — turned out to be a misreading: that file is a 42-byte ASCII
summary written **periodically**, not at the end, so it never described the
final time on either run. The data was fine; the diagnostic was wrong. Recorded
because the retraction cost real time.

**Files.** `build_arm64.py` (builds FDS native), `validate_build.py`,
`compare_hrr.py`, `hrr_divergence.py`, `test_arm64.py`.
