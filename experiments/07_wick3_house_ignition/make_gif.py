#!/usr/bin/env python3
"""Assemble Smokeview-rendered PNG frames into an animated GIF.

Usage:
    make_gif.py <frames_dir> <out.gif> [fps] [pattern]

Frames are sorted by filename, so zero-pad your frame numbers in the .ssf
(frame_06, frame_10, ... rather than frame_6, frame_10).
"""

from __future__ import annotations

import glob
import os
import sys

from PIL import Image


def main() -> None:
    frames_dir = sys.argv[1] if len(sys.argv) > 1 else "images"
    out = sys.argv[2] if len(sys.argv) > 2 else "animation.gif"
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    pattern = sys.argv[4] if len(sys.argv) > 4 else "*.png"

    paths = sorted(glob.glob(os.path.join(frames_dir, pattern)))
    if not paths:
        raise SystemExit(f"no frames matched {frames_dir}/{pattern}")

    images = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in paths]
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=int(1000.0 / fps),
        loop=0,
        optimize=True,
    )
    print(f"wrote {out}  ({len(paths)} frames, {fps:g} fps)")
    for p in paths:
        print("  ", os.path.basename(p))


if __name__ == "__main__":
    main()
