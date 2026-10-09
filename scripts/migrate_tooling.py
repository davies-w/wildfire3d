"""Move the loose tooling out of ~/FDS and into the repository.

~/FDS is the working area: solver, case directories, raw output. Every script
that produced a result, checked a result, or probed the renderer belongs in the
repo instead -- see AGENTS.md rule 1.

Explicit map, no inference. Anything not listed is reported so it can be
classified rather than silently left behind.
"""
import os, shutil, sys

FDS = os.path.expanduser("~/FDS")
REPO = os.path.expanduser("~/pi/wildfire3d")

MAP = {
    "scripts": [
        # storage / HF bucket tooling
        "hf_token_setup.py", "inspect_token_file.py", "rebuild_token_backup.py",
        "hf_anon_test.py", "dvc_hf_roundtrip.py", "setup_dvc.py",
        "verify_anon_pull.py", "verify_fresh_clone.py", "show_gif.py",
        # focus fix
        "make_smv_agent.py", "test_interpose.py",
        # FDS manual reading
        "pdfgrep.py", "pdftxt.py",
        # migration record
        "build_experiments.py",
    ],
    "experiments/01_baseline_garden": [
        "animate_burning.py", "check_flame.py", "check_hrr.py", "fix_terrain.py",
        "plot_fds.py",
    ],
    "experiments/03_vegetation": ["render_big.py"],
    "experiments/04_fence_and_trees_large": [
        "animate_house_risk.py", "render_burning.py", "test_house_risk.py",
        "verify_tall_skirt.py",
    ],
    "experiments/05_ember_lofting": ["fix_tree_surf.py"],
    "experiments/07_wick3_house_ignition": [
        # boundary-data readers -- evidence for the ignition claim
        "read_canopy.py", "probe_bf.py", "diag_canopy.py", "diag_red.py",
        "diag_quad.py", "analyse_clean.py", "wall_profile.py", "wall_times.py",
        "hrr_wick3.py",
        # renderers, earliest to final
        "render_wick.py", "render_wick3.py", "render_wick3_fire.py",
        "render_wick3_late.py", "render_wick3c.py",
        "ign_a.py", "ign_b.py", "rebuild_blend.py", "regen_animation.py",
        "ign_render.py", "ign_blend.py",
        # solvers and deck builders
        "run_clean.py", "run_clean_arm.py", "run_wick3.py", "run_wick3_dev.py",
        "run_wick3_restart.py", "wick3_dev.py", "wick3_restart.py",
        "wick_fence_bndf.py",
    ],
    "experiments/11_smokeview_renderer": [
        "test_headless.py", "test_multiframe.py", "test_noterrain.py",
        "test_smokeprop.py", "test_bounds.py", "test_agent_render.py",
        "measure_house.py",
    ],
}

DELETE = ["hf_s3_check.py", "check_cred_file.py"]   # abandoned S3 route

placed, skipped = [], []
for dest, names in MAP.items():
    out = os.path.join(REPO, dest)
    os.makedirs(out, exist_ok=True)
    for n in names:
        src = os.path.join(FDS, n)
        if os.path.exists(src):
            shutil.copy2(src, out)
            placed.append(n)
        else:
            skipped.append(n)

for n in DELETE:
    p = os.path.join(FDS, n)
    if os.path.exists(p):
        os.remove(p)
        print("deleted (abandoned): %s" % n)

print("placed %d files" % len(placed))
if skipped:
    print("not found (already moved or renamed): %s" % ", ".join(skipped))
