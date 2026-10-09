# 05 — Do firebrands actually leave the boundary layer?

**Question.** FDS generates embers from a burning surface. Do they loft into
the plume where they can travel, or do they sit in the dead air right above the
fuel and go nowhere?

**Setup.** `garden_loft.fds`, plus the `t_*.fds` variants used to isolate the
cause. Level-set mode with `EMBER_YIELD` on the burning surface.

**What happened — and this was a real bug, not a physical result.** Embers
spawned *on* the surface, where the vertical velocity is approximately zero,
and never lifted. The fix is `EMBER_GENERATION_HEIGHT = 1.0, 8.0`, which is the
**lofting model** in level-set mode: embers are born a metre or more above the
fuel and emerge into moving air.

A second, subtler problem: embers spawned at ambient temperature (20–60 °C)
cannot ignite anything. Setting `INITIAL_TEMPERATURE` on the `&PART` **does**
apply to surface-generated particles, contrary to what the documentation
implies — a firebrand material with a huge `SPECIFIC_HEAT` only works if the
ember is born hot.

**Conclusion.** Both are configuration, not physics. Once set, embers loft and
carry temperature. Worth recording because the failure mode looks like a
physics result — "embers don't transport" — and is not.

**Files.** `add_ladder_tree.py`. Results: `fe_050.png` (fire + embers),
`key_house.png`.
