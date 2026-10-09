#!/usr/bin/env python3
"""Retry any missing frames, then blend and build the gifs.

Smokeview intermittently fails a single render, so retry each missing frame up
to three times before giving up.  Multi-frame runs are avoided entirely.
"""
import os
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

TIMES = [8, 16, 24, 32, 40, 50, 62, 76, 92, 110]
PASSES = [("fireembers", ["garden_tall_1_3.s3d", "garden_tall_1.prt5"], "ft"),
          ("smoke", ["garden_tall_1_1.s3d"], "s")]


def render_one(subdir, files, prefix, t):
    with open(os.path.join(CASE, "garden_tall.ssf"), "w") as fh:
        fh.write(f"RENDERDIR\n {subdir}\nUNLOADALL\nLOADINIFILE\n"
                 f" garden_tall.ini\n")
        for f in files:
            fh.write(f"LOADFILE\n {f}\n")
        fh.write(f"SETVIEWPOINT\n iso_b\nSETTIMEVAL\n {t}.0\n"
                 f"RENDERONCE\n {prefix}_{t:03d}\n")
    subprocess.run([SMV, "-runscript", "garden_tall"], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=600)
    return os.path.exists(
        os.path.join(CASE, subdir, f"{prefix}_{t:03d}.png"))


for subdir, files, prefix in PASSES:
    for t in TIMES:
        png = os.path.join(CASE, subdir, f"{prefix}_{t:03d}.png")
        if os.path.exists(png):
            continue
        for attempt in range(3):
            if render_one(subdir, files, prefix, t):
                print(f"  {subdir} t={t}: recovered on attempt {attempt + 1}")
                break
        else:
            print(f"  {subdir} t={t}: STILL MISSING")
    have = len([1 for t in TIMES if os.path.exists(
        os.path.join(CASE, subdir, f"{prefix}_{t:03d}.png"))])
    print(f"{subdir}: {have}/{len(TIMES)}")

subprocess.run([VENV, os.path.expanduser("~/FDS/composite_smoke.py"),
                os.path.join(CASE, "fireembers"), os.path.join(CASE, "smoke"),
                os.path.join(CASE, "composited"), "0.70"], check=False)
for src, gif in (("composited", "tall_fire_smoke.gif"),
                 ("fireembers", "tall_fire_embers.gif")):
    subprocess.run([VENV, os.path.expanduser("~/FDS/make_gif.py"),
                    os.path.join(CASE, src), os.path.join(CASE, gif), "1.0"],
                   check=False)
    p = os.path.join(CASE, gif)
    print(f"  {gif}: {os.path.getsize(p)} bytes"
          if os.path.exists(p) else f"  {gif}: FAILED")
subprocess.run(["open", os.path.join(CASE, "tall_fire_smoke.gif")], check=False)
print("opened")
