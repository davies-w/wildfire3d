"""Populate experiments/ from the working files in ~/FDS.

One-off migration.  Maps each case in ~/FDS/cases to a self-contained experiment
directory: the input deck that produced it, the scripts that ran and analysed
it, and the key rendered results.

Files are copied, not moved -- ~/FDS stays intact until the result is checked.
"""
import os, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

import os, shutil

FDS = FDS_ROOT
REPO = os.path.expanduser("~/pi/wildfire3d")

# name -> deck paths, case dirs, scripts, result paths (all relative to ~/FDS)
PLAN = {
    "01_baseline_garden": (
        ["cases/garden_house/garden_house.fds"], ["garden_house"],
        ["run_case.py", "patch_smv_colors.py", "identify_skirt.py"],
        ["cases/garden_house/images/gh_025.png", "cases/garden_house/images/gh_115.png"]),
    "02_no_lawn_control": (
        ["cases/garden_nolawn/garden_nolawn.fds"], ["garden_nolawn"],
        ["run_case.py"],
        ["cases/garden_nolawn/wallcheck/nolawn_wallT_115.png"]),
    "03_vegetation": (
        ["cases/garden_veg/garden_veg.fds", "cases/garden_veg_obst/garden_veg_obst.fds"],
        ["garden_veg", "garden_veg_obst"],
        ["composite_smoke.py", "diag_smoke.py"],
        ["cases/garden_veg/composited/c_030.png", "cases/garden_veg/wallcheck/ls_100.png"]),
    "04_fence_and_trees_large": (
        ["cases/garden_tall/garden_tall.fds", "cases/garden_tall/wick.fds",
         "cases/garden_tall/house_risk.fds"], ["garden_tall"],
        ["build_tall.py", "run_tall.py", "render_tall.py", "rerender_tall.py",
         "finish_tall.py", "fix_tall_smoke.py", "wick_stage1.py", "wick_stage2.py",
         "wick_stage3.py", "make_house_risk.py", "render_risk.py"],
        ["cases/garden_tall/bigcomposited/c_160.png"]),
    "05_ember_lofting": (
        ["cases/garden_loft/garden_loft.fds"], ["garden_loft"],
        ["add_ladder_tree.py"],
        ["cases/garden_loft/combine/fe_050.png", "cases/garden_loft/key_house.png"]),
    "06_half_metre_ladder": (
        ["cases/wick2/wick2.fds"], ["wick2"],
        ["run_wick2.py", "render_wick2.py", "hrr_wick2.py", "add_ladder_tree.py",
         "wick2_a.py", "wick2_b1.py", "wick2_b2.py", "when_tree.py"],
        ["cases/wick2/composited/c_110.png", "cases/wick2/zoom_110.png"]),
    "07_wick3_house_ignition": (
        ["cases/wick3/wick3c.fds", "cases/wick3/wick3.fds"], ["wick3"],
        ["build_clean.py", "run_clean_arm.py", "analyse_clean.py", "render_wick3c.py",
         "ign_render.py", "ign_blend.py", "strip_terrain.py", "make_gif.py"],
        ["cases/wick3/ignition_clean.gif", "cases/wick3/ignition_clean/i_280.png"]),
    "08_isolated_ember_ignition": (
        ["cases/ember_test/ember_test.fds", "runs/ember_ignition/LS4_ember_ignition.fds",
         "runs/bfm_res_test/bfm_res_test.fds"],
        ["ember_test"],
        ["make_test_variants.py"],
        ["runs/ember_ignition/images/frame_38.png"]),
    "09_benchmarks_and_scaling": (
        ["cases/wick2_bench/bench.fds"], ["wick2_bench", "arm_bench"],
        ["bench_builds.py", "scaling.py", "scaling_arm.py", "ec2_price.py",
         "blob_audit.py", "compress_test.py"],
        []),
    "10_build_validation": (
        ["cases/valid_arm/wtest.fds"], ["valid_arm", "valid_x86"],
        ["build_arm64.py", "validate_build.py", "compare_hrr.py", "hrr_divergence.py",
         "test_arm64.py"],
        []),
}

missing = []
for name, (decks, case_dirs, scripts, results) in sorted(PLAN.items()):
    dest = os.path.join(REPO, "experiments", name)
    os.makedirs(os.path.join(dest, "results"), exist_ok=True)
    for d in decks:
        src = os.path.join(FDS, d)
        if os.path.exists(src):
            shutil.copy2(src, dest)
        else:
            missing.append(d)
    for s in scripts:
        src = os.path.join(FDS, s)
        if os.path.exists(src):
            shutil.copy2(src, dest)
        else:
            missing.append(s)
    for r in results:
        src = os.path.join(FDS, r)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, "results", os.path.basename(r)))
        else:
            missing.append(r)
    n = len(os.listdir(dest)) + len(os.listdir(os.path.join(dest, "results")))
    print("%-28s %2d files" % (name, n))

if missing:
    print("\nmissing:")
    for m in missing:
        print("  " + m)
