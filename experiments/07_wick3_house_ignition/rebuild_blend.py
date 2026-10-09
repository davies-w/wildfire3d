#!/usr/bin/env python3
"""Rename the flame+ember pass frames to the prefix the blender expects,
then rebuild the blended animation from the post-fix frames.

composite_smoke.py globs 'ft_*.png' in the base dir and looks for 's_<tag>'
in the smoke dir, so the base frames must be ft_NNN.png.
"""
import glob
import os
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_loft")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

# 1. rename f_NNN.png -> ft_NNN.png in the flame+ember pass
renamed = 0
for p in sorted(glob.glob(os.path.join(CASE, "fireembers", "f_*.png"))):
    new = os.path.join(os.path.dirname(p),
                       "ft_" + os.path.basename(p)[2:])
    os.rename(p, new)
    renamed += 1
print(f"renamed {renamed} frames to ft_*.png")

# 2. clear the stale blend, then rebuild it
stale = os.path.join(CASE, "composited")
if os.path.isdir(stale):
    for p in glob.glob(os.path.join(stale, "*.png")):
        os.remove(p)
print("cleared stale composited frames")

subprocess.run([VENV, os.path.expanduser("~/FDS/composite_smoke.py"),
                os.path.join(CASE, "fireembers"),
                os.path.join(CASE, "smoke"),
                stale, "0.70"], check=False)

subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                stale, os.path.join(CASE, "fire_embers_smoke.gif"), "1.0"],
               check=False)

g = os.path.join(CASE, "fire_embers_smoke.gif")
print(f"fire_embers_smoke.gif: {os.path.getsize(g)} bytes"
      if os.path.exists(g) else "FAILED")
print("composited frames:", len(glob.glob(os.path.join(stale, "*.png"))))
