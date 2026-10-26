# Public fire report index and simple scorecard

Requested in the side conversation: combine active and quiet 16-second metrics, keep each model's columns together, add the three-state MLP, publish on Hugging Face and preserve in GitHub.

`build.py` reads saved metrics only: it performs no inference, training, selection or threshold changes. `dvc repro` regenerates the report hub and supporting pages under `data/`. Inputs are bounded snapshots of the existing reports; the learning-curve PNGs are existing rendered figures, not raw experimental data.

Sources: `attempt22/data/activity_comparison/report.json` (three-state MLP from attempt18, frozen v1 analysis) and `attempt24/results/scorecard-summary.json` (matched plain/gated four-state GRUs). Source hashes accompany the published simple report. Baseline and truth denominators are checked across experiments. Active percentages are whole numbers; quiet percentages are rounded to one significant digit, without exponents. Exact errors, denominators and units remain expandable and downloadable. No four-state MLP exists; heating is marked not predicted for the MLP.

The index links both existing public fire Spaces and the simplified, detailed, earlier architecture and learning-curve reports. The research findings link points to GitHub. No model checkpoints, raw solver data or unrelated Hugging Face projects are published by this script.

The MLP/GRU comparison spans experiments and is not an isolated architecture ablation. Four-state heating is a surface index, not joules; release is vegetation gas, not combustion heat. Ten grouped test folds, 520 histories/480 configurations, previously examined and reshuffled; not a pristine benchmark. Quiet gas relative errors have almost-zero denominators. Generic 3 m-wide vegetation cones, heights 4/6/8/10 m above a 2 m base, 1600 weighted particles, .5 m mesh in a 24×16×16 m domain, 180 s histories, artificial 1500°C ignition for 20 s, 48 legacy geometries. No trunks/buildings/embers or physical validation. Derived mass states use yield .75; char is inert ash.
