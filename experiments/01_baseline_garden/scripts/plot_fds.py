#!/usr/bin/env python3
"""Plot FDS CSV output.

FDS writes CSV files with *two* header rows: row 1 is units, row 2 is the
quantity names.  ``pandas.read_csv`` and ``np.loadtxt`` both need to know that.

Usage:
    plot_fds.py <run_dir> [output.png]

Reads <CHID>_hrr.csv and <CHID>_devc.csv from <run_dir>, matching whatever CHID
it finds there, and produces a multi-panel summary figure.
"""

from __future__ import annotations

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def read_fds_csv(path: str) -> tuple[list[str], list[str], np.ndarray]:
    """Return (units, names, data) from an FDS CSV file."""
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    if len(rows) < 3:
        raise ValueError(f"{path}: too few rows")
    units, names = rows[0], rows[1]
    data = np.array([[float(x) if x.strip() else np.nan for x in r]
                     for r in rows[2:] if r], dtype=float)
    return units, names, data


def find_chid(run_dir: str) -> str:
    for fn in os.listdir(run_dir):
        if fn.endswith("_hrr.csv"):
            return fn[: -len("_hrr.csv")]
    raise SystemExit(f"no *_hrr.csv found in {run_dir}")


def main() -> None:
    run_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(run_dir, "fds_summary.png")
    chid = find_chid(run_dir)

    hrr_path = os.path.join(run_dir, f"{chid}_hrr.csv")
    devc_path = os.path.join(run_dir, f"{chid}_devc.csv")

    _, hnames, hdata = read_fds_csv(hrr_path)
    t = hdata[:, hnames.index("Time")]

    panels = []
    panels.append(("hrr", hnames, hdata, t))
    if os.path.exists(devc_path):
        _, dnames, ddata = read_fds_csv(devc_path)
        panels.append(("devc", dnames, ddata, ddata[:, dnames.index("Time")]))

    fig, axes = plt.subplots(len(panels), 1,
                             figsize=(9, 3.4 * len(panels)), squeeze=False)

    # --- panel 1: heat release rate and its components
    ax = axes[0][0]
    for key, style in (("HRR", "-"), ("Q_RADI", "--"), ("Q_CONV", ":"),
                       ("Q_PART", "-.")):
        if key in hnames:
            ax.plot(t, hdata[:, hnames.index(key)], style, lw=1.8, label=key)
    ax.set_xlabel("time [s]")
    ax.set_ylabel("power [kW]")
    ax.set_title(f"{chid}: heat release rate")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)

    # --- panel 2: device channels
    if len(panels) > 1:
        _, dnames, ddata, td = panels[1][1], panels[1][1], panels[1][2], panels[1][3]
        ax = axes[1][0]
        cmap = plt.get_cmap("tab10")
        for i, name in enumerate(dnames):
            if name == "Time":
                continue
            ax.plot(td, ddata[:, i], lw=1.8, color=cmap((i - 1) % 10), label=name)
        ax.set_xlabel("time [s]")
        ax.set_ylabel("device value (see CSV units)")
        ax.set_title(f"{chid}: devices")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")
    print(f"  Time range: {t.min():.1f} - {t.max():.1f} s")
    if "HRR" in hnames:
        hrr = hdata[:, hnames.index("HRR")]
        print(f"  Peak HRR  : {np.nanmax(hrr):.2f} kW at t="
              f"{t[np.nanargmax(hrr)]:.1f} s")


if __name__ == "__main__":
    main()
