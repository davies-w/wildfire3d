#!/usr/bin/env python3
"""Build two short (T_END=5) variants of the garden case to identify the
olive 'skirt' at the base of every obstruction.

  t_magenta : the GRASS surface is given a garish RGB *in the FDS input*.
              If the skirt turns magenta, the skirt IS the GRASS surface
              (and my earlier .smv patch was simply faulty).
              If the skirt stays olive, it is NOT the GRASS surface.

  t_lawnall : the LAWN vent is extended to cover the whole domain, so no
              ground cell can fall back to the domain default surface.
              If the skirt disappears, it is default-surface fallback.
"""
import os

src = os.path.expanduser("~/FDS/cases/garden_loft/garden_loft.fds")
base = open(src).read()

# --- variant 1: make the GRASS surface unmistakable, in the solver input
a = (base
     .replace("CHID='garden_loft'", "CHID='t_magenta'")
     .replace("T_END=120.", "T_END=5.")
     .replace("RGB        = 138,129,62", "RGB        = 255,0,255"))
open(os.path.expanduser("~/FDS/cases/garden_loft/t_magenta.fds"), "w").write(a)

# --- variant 2: extend the LAWN patch over the entire ground plane
lawn_line = "&VENT XB=16.0,40.0, 12.0,28.0, 0.0,0.0, SURF_ID='LAWN' /"
lawn_all = "&VENT XB=0.0,40.0, 0.0,40.0, 0.0,0.0, SURF_ID='LAWN' /"
b = (base
     .replace("CHID='garden_loft'", "CHID='t_lawnall'")
     .replace("T_END=120.", "T_END=5.")
     .replace(lawn_line, lawn_all))
open(os.path.expanduser("~/FDS/cases/garden_loft/t_lawnall.fds"), "w").write(b)

print("wrote t_magenta.fds and t_lawnall.fds")
print("  magenta variant: GRASS RGB 138,129,62 -> 255,0,255 ?",
      "255,0,255" in a)
print("  lawnall variant: LAWN vent extended      ?",
      lawn_all in b)
