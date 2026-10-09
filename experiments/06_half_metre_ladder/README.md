# 06 — Half-metre cells: a tree ignites and takes over

**Question.** Experiments 01–04 used 1 m cells. What changes at 0.5 m?

**Setup.** `wick2.fds`. 40 × 40 × 12 m, **0.5 m cells** (153,600 cells), 120 s.
Same garden plus a "ladder" tree.

**What happened.** The **ladder tree ignites**, and the heat release rate
**rises continuously to ~60 MW** instead of peaking and decaying. This is the
first case in which the fire sustains itself on a structure rather than on
prescribed fuel.

**Conclusion — the key structural finding.** Finer cells do not merely refine
the same picture; they change the mechanism. At 1 m a tree is one or two cells
and cannot support a fire that spreads within itself. At 0.5 m it becomes a
sequence of fuel cells with a temperature gradient along it, which is what a
ladder fuel is. That is why 07 is at 0.5 m.

Cost: 153,600 cells ran 120 s in ~3,150 s (26.3 s per simulated second) on the
MPI build. See `docs/performance.md` — the native arm64 build is substantially
faster than what this case was originally run on.

**Files.** `add_ladder_tree.py` builds the tree; `run_wick2.py` solves;
`render_wick2.py` renders; `hrr_wick2.py` extracts HRR; `when_tree.py` finds the
ignition time; `wick2_a.py`, `wick2_b1.py`, `wick2_b2.py` are the staged builder.
Results: `c_110.png`, `zoom_110.png`.
