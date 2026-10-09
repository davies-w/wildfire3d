#!/usr/bin/env python3
"""Blend a Smokeview flame render with a matching smoke render.

Smokeview's 3-D smoke renders saturated (opaque black) once the plume outgrows
the domain, and the opacity control is GUI-only -- there is no script command
for it.  So instead we render the flame and the smoke as two separate passes
from an identical camera, then blend:

    out = w * base + (1 - w) * smoke

Where there is no smoke the two passes are identical, so the blend leaves the
image untouched.  Where smoke is dense the smoke pass is black, so the result
becomes ``w * base``: the scene shows through at ``w``, which reads as
translucent smoke.

Usage:  composite_smoke.py <base_dir> <smoke_dir> <out_dir> [weight]
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    base_dir = sys.argv[1]
    smoke_dir = sys.argv[2]
    out_dir = sys.argv[3]
    w = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55

    os.makedirs(out_dir, exist_ok=True)
    # clear stale frames, otherwise output from an earlier case gets mixed in
    for stale in glob.glob(os.path.join(out_dir, "*.png")):
        os.remove(stale)
    bases = sorted(glob.glob(os.path.join(base_dir, "ft_*.png")))
    if not bases:
        raise SystemExit(f"no ft_*.png in {base_dir}")

    made = 0
    for b in bases:
        tag = os.path.basename(b)[3:]                 # 'ft_006.png' -> '006.png'
        s = os.path.join(smoke_dir, f"s_{tag}")
        if not os.path.exists(s):
            print(f"  no smoke pass for {tag}, skipping")
            continue
        A = np.asarray(Image.open(b).convert("RGB"), dtype=float)
        B = np.asarray(Image.open(s).convert("RGB"), dtype=float)
        if A.shape != B.shape:
            print(f"  size mismatch for {tag}, skipping")
            continue
        out = np.clip(w * A + (1.0 - w) * B, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(os.path.join(out_dir, f"c_{tag}"))
        made += 1

    print(f"blended {made} frames at weight {w:.2f} -> {out_dir}")


if __name__ == "__main__":
    main()
