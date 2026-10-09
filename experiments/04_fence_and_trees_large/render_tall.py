#!/usr/bin/env python3
"""Render the three-layer animation for the taller (24 m) garden case.

Structure is the same as the 12 m case:
  pass 1  flame volume + embers  -> fireembers/  (prefix ft_ so the blender
                                                   can pair them with s_*)
  pass 2  soot volume            -> smoke/
  blend   0.70*pass1 + 0.30*pass2 -> composited/  ("light smoke")
then build the gifs and open the blended one.
"""
import os
import shutil
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

TIMES = [8, 16, 24, 32, 40, 50, 62, 76, 92, 110]


def write_ssf(name, subdir, files, prefix, times):
    path = os.path.join(CASE, f"{name}.ssf")
    with open(path, "w") as fh:
        fh.write(f"RENDERDIR\n {subdir}\nUNLOADALL\nLOADINIFILE\n"
                 f" garden_tall.ini\n")
        for f in files:
            fh.write(f"LOADFILE\n {f}\n")
        fh.write("SETVIEWPOINT\n iso_b\n")
        for t in times:
            fh.write(f"SETTIMEVAL\n {t}.0\nRENDERONCE\n {prefix}_{t:03d}\n")
    return path


def render(name, subdir):
    out = os.path.join(CASE, subdir)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    subprocess.run([SMV, "-runscript", name], cwd=CASE,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL, timeout=1500)
    n = len(os.listdir(out))
    print(f"  {subdir}: {n} frames")
    return out


write_ssf("garden_tall", "fireembers",
          ["garden_tall_1_3.s3d", "garden_tall_1.prt5"], "ft", TIMES)
render("garden_tall", "fireembers")

write_ssf("smokepass", "smoke", ["garden_tall_1_1.s3d"], "s", TIMES)
render("smokepass", "smoke")

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
print("opened tall_fire_smoke.gif")
