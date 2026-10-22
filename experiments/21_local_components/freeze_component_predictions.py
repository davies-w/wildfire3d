"""Freeze standalone inference code, chosen model and two test predictions. No FDS solve."""
import hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from scene import ROOT

def main():
 model_path=ROOT/sys.argv[1];selection=ROOT/'results/component-model-selection.json';assert selection.exists(),'Record model selection and limitations first'
 decision=json.loads(selection.read_text());assert decision['model_sha256']==hashlib.sha256(model_path.read_bytes()).hexdigest()
 dest=ROOT/'data/component_frozen';assert not dest.exists(),'Never overwrite a frozen prediction set';dest.mkdir()
 sources=['component_model.py','component_hot_state_model.py','component_heat_rule.py','component_release_rule.py','diagnose_wall_response.py','evaluate_recursive_canopy_energy_budget.py','component_occlusion.py','component_metrics.py','analyze_component_tests.py','component_additive_baseline.py','scene.py']
 for src in sources:shutil.copy2(ROOT/src,dest/src)
 shutil.copy2(ROOT/'data/additive_baseline.json',dest/'baseline.json');shutil.copy2(model_path,dest/'model.json');shutil.copy2(ROOT/'component-test-inputs.json',dest/'test-inputs.json');shutil.copy2(selection,dest/'selection.json')
 runner='''import copy,json,time,hashlib\nfrom pathlib import Path\nimport numpy as np\nfrom component_model import geometry\nfrom component_occlusion import apply\nfrom evaluate_recursive_canopy_energy_budget import rollout\nfrom component_additive_baseline import rollout as additive_rollout\nroot=Path(__file__).resolve().parent;model=json.loads((root/'model.json').read_text());additive=json.loads((root/'baseline.json').read_text());tests=json.loads((root/'test-inputs.json').read_text())['cases'];rows=[]\nfor c in tests:\n for label in ['graph','baseline','ablation']:\n  start=time.perf_counter();g=geometry(c,c['extra_surface_patches'])\n  if model.get('occlusion',False):g=apply(g,c)\n  if label=='ablation':\n   for i,n in enumerate(g['nodes']):\n    if n['kind']=='vegetation':g['kernel'][i,:]=0\n  r=(additive_rollout(additive,g,c['horizon_s']) if label=='baseline' else rollout(model,g,c['horizon_s']));elapsed=time.perf_counter()-start;path=root/(c['case']+'-'+label+'.npz');np.savez_compressed(path,**r);b=np.array([n['kind']=='building' for n in g['nodes']]);hit=np.flatnonzero(r['state'][:,b,0].max(1)>=350);rows.append(dict(case=c['case'],model=label,nodes=len(g['nodes']),surface_nodes=int(b.sum()),seconds_including_geometry=elapsed,predicted_ignition_s=float(r['time'][hit[0]]) if len(hit) else None,predicted_peak_C=float(r['state'][:,b,0].max()),prediction_file=path.name));print(rows[-1],flush=True)\n(root/'prediction-summary.json').write_text(json.dumps(dict(results=rows,scope='90s autonomous predictions, single CPU thread, including geometry excluding model load. Baseline is separately fitted on single-canopy training curves and adds source heat without canopy-to-canopy ignition. Additional ablation suppresses incoming canopy messages using graph weights. Neither uses FDS values during prediction. No FDS values used. Surfaces sampled sparsely; full-scene any-part ignition remains the FDS criterion.'),indent=2))\n'''
 (dest/'predict.py').write_text(runner)
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
 subprocess.run([sys.executable,str(dest/'predict.py')],env=env,check=True)
 files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()}
 for c in json.loads((ROOT/'component-test-inputs.json').read_text())['cases']:
  p=ROOT/'decks'/f"{c['case']}.fds";files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 out=dict(frozen_unix=time.time(),frozen_utc=datetime.now(timezone.utc).isoformat(),cases=[c['case'] for c in json.loads((ROOT/'component-test-inputs.json').read_text())['cases']],files=files,selection=decision,rule='No model, baseline, test geometry or prediction changes after this freeze. No test FDS output was accessed during generation.')
 (ROOT/'results/component-test-prediction-freeze.json').write_text(json.dumps(out,indent=2));print('FROZEN; no cloud launch')
if __name__=='__main__':main()
