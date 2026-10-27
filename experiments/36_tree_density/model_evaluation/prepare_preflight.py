"""Prepare cloud-only timing inputs and offline checks; never submit compute."""
from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parents[1];OLD=R.parent/'35_surrogate_diagnostics/attempt25'
def main():
 assert json.loads((R/'results/dataset-completeness.json').read_text())['passed']
 assert json.loads((R/'results/model-data-preflight.json').read_text())['passed']
 dest=R/'data/model-preflight';(dest/'data').mkdir(parents=True,exist_ok=True);(dest/'results').mkdir(exist_ok=True)
 for name in ('worker.py','model.py'):shutil.copyfile(R/'data/model-runner'/name,dest/name)
 shutil.copyfile(R/'data/learning/sequences.npz',dest/'data/sequences.npz');shutil.copyfile(R/'learning-schema.json',dest/'schema.json')
 plan=json.loads((OLD/'coverage-plan.json').read_text());plan.pop('learning_curve')
 plan.update(experiment='Density36 cloud preflight and timing only',selection='All ten validation selections frozen before tests in later training',test='No test evaluation in this preflight',budget={'soft_seconds':900,'maximum_allowance_usd':.5},save_forecasts=False)
 (dest/'coverage-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 runtime=(OLD/'runtime.py').read_text();assert runtime.count("PREFIX='diagnostics35/attempt25/'")==1
 (dest/'runtime.py').write_text(runtime.replace("PREFIX='diagnostics35/attempt25/'","PREFIX='density36/model-preflight01/'"))
 source=(OLD/'validate.py').read_text();body=source[source.index('dt=times[:,1:]'):source.index("(R/'results/preflight.json')")]
 header="from pathlib import Path\nimport json,io,ast\nimport numpy as np\nimport torch\nfrom model import Transition,normalize_fit\ntorch.set_num_threads(4);R=Path(__file__).resolve().parent;meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/sequences.npz');raw=torch.tensor(a['state']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry'])\nassert raw.shape==(2080,91,4) and geom.shape==(2080,7)\n"
 footer="(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,local_training=False,histories=2080,configurations=2040,checks=checks),indent=2));print('RUNNER PREFLIGHT PASSED')\n"
 (dest/'validate.py').write_text(header+body+footer)
 for name in ('validate_evaluation.py','validate_transport.py'):shutil.copyfile(OLD/name,dest/name)
 shutil.copyfile(R/'model_evaluation/time_cloud.py',dest/'time_cloud.py')
 hashes={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file() and 'results' not in p.relative_to(dest).parts}
 (R/'results/model-preflight-inputs.json').write_text(json.dumps({'files':hashes,'submitted':False,'training':False,'output_prefix':'density36/model-preflight01/','maximum_proposed_allowance_usd':.5,'allowance_source':'Existing $8 model reservation, not additional unreserved spending'},indent=2)+'\n')
 print('Prepared; no cloud launch')
if __name__=='__main__':main()
