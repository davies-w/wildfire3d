#!/usr/bin/env python3
"""Re-render the taller garden animation after the terrain strip.

Both passes are rendered ONE FRAME PER SMOKEVIEW INVOCATION.  Multi-frame runs
of the large volume files crash Smokeview intermittently, and suppressing their
output hides the failure.

Frame naming: the flame+ember pass uses ft_NNN.png because composite_smoke.py
pairs 'ft_NNN.png' in the base dir with 's_NNN.png' in the smoke dir.
"""
import os
import shutil
import subprocess

CASE = os.path.expanduser("~/FDS/cases/garden_tall")
SMV = os.path.expanduser("~/FDS/FDS-6.11.1_SMV-6.11.2_osx/smvbin/smokeview")
VENV = os.path.expanduser("~/FDS/.venv/bin/python")

TIMES = [8, 16, 24, 32, 40, 50, 62, 76, 92, 110]


def render_pass(subdir, files, prefix):
    out = os.path.join(CASE, subdir)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    ok = 0
    for t in TIMES:
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
        ok += os.path.exists(os.path.join(out, f"{prefix}_{t:03d}.png"))
    print(f"  {subdir}: {ok}/{len(TIMES)} frames")
    return ok


n1 = render_pass("fireembers", ["garden_tall_1_3.s3d", "garden_tall_1.prt5"], "ft")
n2 = render_pass("smoke", ["garden_tall_1_1.s3d"], "s")

if n1 == n2 == len(TIMES):
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
