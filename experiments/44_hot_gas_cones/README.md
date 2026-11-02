# Five-parameter hot-gas cones

A target-free geometric compression of **48 existing development histories / 4,368 saved frames**. No new simulation, neural training, optimizer update, or paid compute. Source: experiment35 attempt10 decoded fields; the earlier attempt11 2σ ovoid is retained as a comparison. These are historically examined data (8 train,40 validation), not untouched tests.

Each active frame has exactly five values: effective apex height in metres, tilt from vertical in degrees, axial length in metres, end radius in metres, and maximum saved gas temperature inside the cone in °C. The apex is constrained to the tree centreline (8,8,h); the axis lies in the +x/z plane, leaning along the supplied wind direction. No targets are inputs. No cone is invented for frames with no gas above50°C.

**Time limitation:** saved times are about2s apart (observed1.813–2.195s). These are instantaneous saved-frame maxima, NOT maxima over the intervening interval. Temperature is neither heat-release rate nor incident heat flux.

## Fit and evidence

Fit to cell centres above50°C, aiming to enclose at least95% by cell count. Search apex at ground level or seven heights within the crown, tilt0–90° in10° increments. At most1,024 deterministic sampled hot cells rank candidates; recalibrate the best eight candidates using ALL hot cells, then select the smallest analytic cone volume among them. This is a coarse geometric search, not a claim of global optimality. End length reaches the furthest forward hot centre; radius supplies the requested coverage. No temporal smoothing.

1,428 frames contain hot gas. Median metrics across active frames:

| Shape | Hot cells captured | Enclosed cells that are hot | Intersection-over-union |
|---|---:|---:|---:|
| Five-parameter cone |95.2%|20.3%|20.1%|
| Original temperature-weighted2σ ovoid |63.6%|—|49.8%|
| Same ovoid expanded to95% coverage |95.1%|38.8%|38.1%|

**The cone covers the hot gas but is usually too broad.** It selects a ground-level apex in83.6% of active frames; that is a fitting compromise, not a physical fire pivot. After the imposed igniter is off, cone purity is22.7%, versus42.1% for the equal-coverage ovoid. The ovoid has a free3D centre/orientation/axis ratios and therefore more geometric freedom; this does not isolate a single shape choice. These are frame medians, not equal-configuration-weighted scores.

The cone misses the domain's hottest cell in123 active frames; its fifth parameter is explicitly the maximum INSIDE the fitted cone. A maximum temperature does not specify the temperature distribution. All metrics use3D masks in the observed domain. The cone may extend beyond that domain, and hot gas can touch its boundaries: no claim about unobserved gas is made. At0.5m resolution this is cell-centre coverage, not a continuous enclosing surface.

## Geometry and physical omissions

Generic conical vegetation crowns3m wide,4/6/8/10m tall, above2m;0.5m grid in24×16×16m; artificial1500°C source for20s. No trunks, buildings or embers. The hot field includes the artificial igniter and heated gas; it is not isolated tree combustion.50°C is a diagnostic threshold, not ignition. No receiver heat flux, radiation field, material ignition, or physical validation is inferred.

## Inspect and reproduce

[Open the published comparison](https://wdavies-fire-state-storyboards.static.hf.space/cones44/index.html), or open `data/report.html`: all48 storyboards plus every frame's five values and comparison metrics. White triangle = cone side projection; magenta = original2σ oval; colours = maximum gas temperature through y, clipped at1000°C. Numeric scores are3D, not measured from those projections.

From this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ../../.venv/bin/python prepare.py
../../.venv/bin/python report.py
../../.venv/bin/python validate.py
../../.venv/bin/python test_cones.py
```

`dvc.yaml` declares these local stages; source files are hash-recorded and outputs use `dvc.lock`. Use the repository's `scripts/dvc_hf.py` for direct HF artifact pushes. Original simulation fields, checkpoints and previous reports are unchanged.


## All rotation-0 training data

The subsequent full extraction covers **all 1,662 frozen rotation-0 training histories / 151,242 saved frames**, from 1,632 physical configurations. This is separate from the 48-history pilot above: no validation or test histories enter the new training dataset. It uses 1,255 retained local temperature slices and 407 existing local archives. Entire source files are SHA-256 checked; all 91 timestamps per history match the frozen learning sequences. A reference archive decode was also compared cell-for-cell against the earlier decoder (91 frames, exact equality). No source data were changed, no new simulations or neural training were run, and no second full-field copy was retained.

[Inspect the complete training extraction and download its arrays](https://wdavies-fire-state-storyboards.static.hf.space/cones44/training/index.html).

There are **57,059 active frames and 94,183 inactive frames**. Every history has at least one active frame, including the imposed ignition period. Active-frame medians:

| Shape | Hot-cell capture | Purity | IoU |
|---|---:|---:|---:|
| Five-parameter cone |95.16%|20.47%|20.30%|
| Original 2σ ovoid |64.23%|75.74%|49.83%|
| Ovoid expanded to 95% coverage |95.11%|36.73%|36.10%|

After the 20 s imposed ignition period, median cone purity is 23.13%, versus 39.53% for the equal-coverage ovoid. Ground-level apex is selected in 86.81% of active frames. The cone misses the domain peak in 6,222 active frames; 21,397 active frames have hot gas on an observed-domain boundary. The cone is a broad hot-gas envelope, not an identified physical flame pivot. All active cones pass the 95% cell-count capture check. The ovoid has additional geometric freedom, so this is not a matched-complexity comparison.

`data/training-summary/targets.npz` contains case indices, timestamps, five parameters, an active mask, and cone/ovoid overlap metrics. Parameters have shape `(1662, 91, 5)` in the order recorded in `parameter-schema.json`. Inactive targets are NaN and must be masked, not treated as zero-valued cones. `histories.json` records exact source and output hashes; `validation.json` proves case coverage, split isolation and timestamp checks. Saved intervals span 1.801–2.195 s; temperatures remain instantaneous, not interval maxima. The original pilot artifacts are unchanged.

### Loss considerations after extraction

No loss has been selected, implemented or tested. The extracted data suggest a candidate baseline with two parts: predict active/inactive, then compare the five values only on active frames. Normalize each parameter separately using training-only scales; raw squared error would let degrees and especially °C dominate metre-valued geometry merely because of their units. A normalized Huber penalty is worth testing because unusually large discrepancies need not dominate as strongly as squared error. Its scales, transition point and activity weight still require a deliberate experiment.

Parameter matching alone is insufficient evidence of a good envelope. Adjacent active-frame angle changes have a 99th percentile of 70°, and pivot changes 3.33 m; these can reflect switching among coarse geometric candidates, not physical jumps. Compare predicted spatial capture and over-coverage as well as parameter errors, retain inactive-frame accuracy, and report sequence/configuration-weighted scores. Do not impose temporal smoothing without testing whether it erases real changes. There are 1,545 active frames (2.71%) with fitted axial length below one 0.5 m cell, down to 0.00020 m. These are degenerate geometric fits to cell centres, not physically resolved flame dimensions; retain and flag them rather than silently treating them as precise labels. The low purity is already a representation limitation; changing a neural loss cannot make the fitted target cones physically precise. Maximum temperature still does not determine receiver heat flux or heat dose.

### Repeat the training-only extraction

From the repository root:

```sh
.venv/bin/python experiments/44_hot_gas_cones/prepare_training.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/44_hot_gas_cones/extract_training.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/44_hot_gas_cones/summarize_training.py
.venv/bin/python experiments/44_hot_gas_cones/report_training.py
.venv/bin/python experiments/44_hot_gas_cones/preserve_training.py
.venv/bin/python experiments/44_hot_gas_cones/publish_training.py
.venv/bin/python experiments/44_hot_gas_cones/verify_training_publication.py
```

Extraction resumes only identical-source/identical-recipe completed histories. The preservation script records output and dependency hashes in `dvc.lock`, uploads original derived files directly to the HF DVC bucket, and saves per-stage remote verification receipts. It creates no persistent cache or local mirror. Publication adds the complete training page and a link from the existing cone comparison without removing older pages.
