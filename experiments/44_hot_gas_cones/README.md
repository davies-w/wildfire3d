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

Open `data/report.html`: all48 storyboards plus every frame's five values and comparison metrics. White triangle = cone side projection; magenta = original2σ oval; colours = maximum gas temperature through y, clipped at1000°C. Numeric scores are3D, not measured from those projections.

From this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ../../.venv/bin/python prepare.py
../../.venv/bin/python report.py
../../.venv/bin/python validate.py
../../.venv/bin/python test_cones.py
```

`dvc.yaml` declares these local stages; source files are hash-recorded and outputs use `dvc.lock`. Use the repository's `scripts/dvc_hf.py` for direct HF artifact pushes. Original simulation fields, checkpoints and previous reports are unchanged.
