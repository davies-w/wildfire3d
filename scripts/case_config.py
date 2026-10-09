"""Per-case configuration for the fire rendering pipeline.

Everything that varies between cases lives in one JSON file beside the deck, so
the tools in scripts/ contain no case knowledge at all.  A config looks like:

    {
      "case": "wick4",                  // directory under FDS/cases
      "chid": "wick4",                  // FDS CHID / output prefix
      "t_end": 300,
      "times": [16, 24, ...],           // frame times, multiples of DT_BNDF
      "smokeprop": 1800,                // mass extinction coefficient, m2/kg
      "surfaces": {
        "FENCE": {"boxes": [[10.99, 11.49, 0.0, 18.01, 12.01, 2.01]],
                  "ignition": 300.0, "rgb": [150, 110, 70]}
      }
    }

A box is (xlo, ylo, zlo, xhi, yhi, zhi): low triplet then high triplet.
A surface may list several disjoint boxes; they must not overlap, or one patch
would drive two surfaces' colours at once (surface_temp.py checks this).
"""
import json, os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402


def load(path):
    """Read a case config and resolve its paths."""
    with open(path) as fh:
        cfg = json.load(fh)

    case_dir = os.path.join(FDS_ROOT, "cases", cfg["case"])
    cfg["case_dir"] = cfg.get("case_dir") or case_dir
    case_dir = cfg["case_dir"]
    chid = cfg["chid"]
    cfg.setdefault("t_end", max(cfg["times"]))
    cfg.setdefault("smokeprop", 300.0)
    cfg.setdefault("out_dir", "igncol")
    cfg["smv"] = os.path.join(case_dir, chid + ".smv")
    cfg["smv_keep"] = os.path.join(case_dir, chid + ".smv.orig")
    cfg["ini"] = os.path.join(case_dir, chid + ".ini")
    cfg["view_ini"] = os.path.join(case_dir, chid + "_view.ini")
    cfg["ssf"] = os.path.join(case_dir, chid + ".ssf")
    cfg["gif"] = os.path.join(case_dir, cfg.get("gif_name", "ignition_data.gif"))
    cfg["out"] = os.path.join(case_dir, cfg["out_dir"])
    cfg["volumes"] = [chid + "_1_1.s3d", chid + "_1_3.s3d", chid + "_1.prt5"]
    cfg["config_path"] = os.path.abspath(path)
    return cfg
