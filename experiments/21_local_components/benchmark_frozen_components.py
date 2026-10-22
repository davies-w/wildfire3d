"""Benchmark unchanged frozen model with and without reusable geometry construction."""
import cProfile,json,os,pstats,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if '--child' not in sys.argv:
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
 subprocess.run([sys.executable,__file__,'--child'],env=env,check=True);raise SystemExit
sys.path.insert(0,str(ROOT/'data/component_frozen'))
from component_model import geometry
from component_occlusion import apply
from evaluate_recursive_canopy_energy_budget import rollout
import numpy as np
frozen=ROOT/'data/component_frozen';m=json.loads((frozen/'model.json').read_text());rows=[]
for c in json.loads((frozen/'test-inputs.json').read_text())['cases']:
 start=time.perf_counter();g=apply(geometry(c,c['extra_surface_patches']),c);build=time.perf_counter()-start;times=[]
 for _ in range(3):
  start=time.perf_counter();r=rollout(m,g,c['horizon_s']);times.append(time.perf_counter()-start)
 with np.load(frozen/(c['case']+'-graph.npz')) as expected:
  delta=max(float(np.max(abs(r[k]-expected[k]))) for k in ['state','heat','time']);assert delta<1e-8
 rows.append(dict(case=c['case'],geometry_seconds=build,reused_geometry_rollout_seconds=times,max_difference_from_frozen_prediction=delta))
(ROOT/'results/frozen-component-speed-breakdown.json').write_text(json.dumps(dict(results=rows,scope='Unchanged frozen weights/code. Reuse geometry only for identical layout,wind and source placement; source states reset each rollout. Single CPU thread,90s physical horizon. No FDS output used.'),indent=2));print(json.dumps(rows,indent=2))
