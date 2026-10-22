from pathlib import Path
import shutil,json,yaml
root=Path(__file__).resolve().parents[1]; a=root/'experiments/35_surrogate_diagnostics'; old=root/'experiments/33_representation_loss/attempt15'
a.mkdir(exist_ok=False);(a/'data/resume').mkdir(parents=True);(a/'results').mkdir()
for n in ['original_cnn.py','geometry_model.py','deterministic_interpolation.py','validate_interpolation.py','fields.py','fortran_records.py','material_reader.py','preprocess_cloud.py','snapshot_evaluation.py']:
 shutil.copy2(old/n,a/n)
for n in ['cloud.py','launch.py','collect.py','prepare_pilot.py']:
 s=(old/n).read_text().replace('pilot15','diag35-01').replace('gpu33-diag35-01','gpu35-diag01').replace('repair33/diag35-01','diagnostics35/attempt01')
 s=s.replace("R.parent.parent/'32_tree_expansion", "R.parent/'32_tree_expansion")
 s=s.replace("R.parent/'data/budget.lock'", "R.parent/'33_representation_loss/data/budget.lock'")
 if n=='cloud.py':s=s.replace("(R.parent/n) if n=='budget.json'", "(R.parent/'33_representation_loss'/n) if n=='budget.json'")
 if n=='launch.py':
  s=s.replace('+3.0','+4.5').replace('allowance_usd=3.0','allowance_usd=4.5').replace('compute_allowance_usd=1.2','compute_allowance_usd=1.6').replace('ancillary_cleanup_allowance_usd=1.8','ancillary_cleanup_allowance_usd=2.9')
 if n=='prepare_pilot.py':
  s=s.replace(",R/'data/initial_snapshot.pt'",'').replace("+ 5400","+ 7200").replace('+ 3900','+ 5700').replace("'3600s'","'5400s'").replace('proposed_new_cap_usd=3.0','proposed_new_cap_usd=4.5').replace('task_deadline_s=3600','task_deadline_s=5400').replace('vm_age_limit_s=3900','vm_age_limit_s=5700').replace('absolute_deadline_s=5400','absolute_deadline_s=7200')
  s=s.replace("runpy.run_path(str(p/'preprocess_cloud.py'),run_name='__main__');runpy.run_path(str(p/'worker.py'),run_name='__main__')", "\ntry:\n runpy.run_path(str(p/'preprocess_cloud.py'),run_name='__main__');runpy.run_path(str(p/'worker.py'),run_name='__main__')\nexcept BaseException:\n import traceback\n from runtime import upload\n upload('bootstrap-error.txt',traceback.format_exc().encode());raise")
 (a/n).write_text(s)
(a/'setup_inputs.py').write_text('''from pathlib import Path
import json,numpy as np
R=Path(__file__).parent; S=R.parent/'32_tree_expansion';P=R.parent/'33_representation_loss/attempt14/results/coverage-summary.json'
cs=json.loads((S/'development.json').read_text());mm={r['configuration']:r['metrics']['truth_mean_HRR_kW'] for r in json.loads(P.read_text())['configuration_metrics'] if r['arm']=='expand360' and r['stage']=='final' and r['cohort']=='all_train360' and r['window']=='post_source'}
rng=np.random.default_rng(3501);names=[]
for lo,hi in [(0,1),(1,10),(10,100),(100,float('inf'))]:names+=list(rng.choice(sorted(k for k,v in mm.items() if lo<=v<hi),2,replace=False))
train=[c for c in cs if c['split']=='train' and c['new_geometry'] and c['replica']==0 and c['configuration'] in names];val=[c for c in cs if c['split']=='validation' and c['new_geometry']];chosen=train+val;assert len(train)==8 and len(val)==40
(R/'cases.json').write_text(json.dumps(chosen,indent=2));groups=json.loads((S/'groups.json').read_text());wanted={c['case'] for c in chosen};(R/'groups.json').write_text(json.dumps([g for g in groups if wanted.intersection(g['cases'])],indent=2));z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in wanted})
plan=dict(seed=3501,single_case=next(c['case'] for c in train if c['configuration']==names[6]),train_configurations=names,epochs={'single':80,'eight':20,'oracle':20,'source':100},loss='Equal-channel normalized MAE in existing encoded variables; scales are training8 encoded population std floored at0.05. No auxiliary penalties.',epoch='Every nonoverlapping three-frame window of every training trajectory, final short window retained; shuffled without replacement.',diagnostic_threshold='Normalized training MAE <=0.05 is a prespecified representability target, not physical fidelity. Report per-channel and physical metrics regardless.',scope='Fresh weights; same base initialization for eight and oracle (extra oracle input weights zero). Oracle sees instantaneous true total FDS HRR, log1p / training-only scale, NOT deployable. Source MLP predicts total HRR separately. All32 previously examined validation configs40trajectories each epoch; no pristine test. Fixed8 deliberately TRAIN-strength-stratified configs. Repeated seed differences are descriptive, not a proved error floor.')
(R/'coverage-plan.json').write_text(json.dumps(plan,indent=2))
''')
(a/'runtime.py').write_text('''import json,urllib.request,urllib.parse
from pathlib import Path
import numpy as np,torch
from original_cnn import cond
from geometry_model import features
R=Path(__file__).parent
PREFIX='diagnostics35/attempt01/'
def upload(n,data):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(req,timeout=20))['access_token'];url='https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+n,safe='');urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST'),timeout=180).read()
def inputs(c,t,g):
 return torch.from_numpy(np.concatenate([cond(c,t),np.repeat(features(g)[None],len(t),0),np.full((len(t),1),(c['moisture']-.12)/.18,np.float32)],1)).cuda()
''')
(a/'README.md').write_text('''# Experiment35: identify the surrogate bottleneck before adding losses

Fresh-start fitting diagnostics, not another warm-start loss sweep. One trajectory80 full epochs; eight TRAIN configurations (two randomly selected per training HRR band)20 full epochs. Compare same initial GeometryCNN against an oracle with true instantaneous FDS total HRR as an additional input; its extra input weights start at zero. Separately fit a scalar HRR MLP100 epochs. Oracle performance is a diagnostic upper-information comparison, not a deployable forecast. All32 previously examined validation configurations40trajectories are evaluated after EVERY epoch; full train set for each arm too. Each epoch covers each saved frame exactly once in nonoverlapping three-frame batches, including the final short batch. Average training losses are frame-weighted, all six normalized encoded channels equally weighted. Training8-only std with0.05 floor; no custom regional, temporal, radiation, or total-HRR penalties. AdamW with cosine decay1e-3→1e-5. Training MAE<=0.05 standardized units is a prespecified fitting target, not proof of physical fidelity or convergence. Plot all curves and late slopes, do not automatically call a capped run saturated. Source predictor uses scaled physical HRR MAE; report weak-fire absolute/relative errors. Seed comparison uses8 existing validation replica pairs without fitting to them; not an asserted irreducible floor.

One fully reserved4.50USD cloud attempt, cumulative74.60/75; retain all failed reservations, invoice unknown. No laptop training/newFDS. Expected45–80minutes after allocation;20minqueue,90mintask,95minVM,120minabsolute cloud deadlines. Checkpoint after each epoch and every250updates with model, optimizer, scheduler, RNG, schedule position, and partial epoch aggregate; resume tested by serialization/forward replay on CUDA. Interrupted work is retained; replacement requires separate allowance. No automatic retries. Collector verifies job/VM/disk cleanup and removes exact temporary read grant. Future paid phases are conditional on evidence and remaining budget.

Simulation scope:3m-wide generic conical crowns4/6/8/10m tall above2m,1600weighted particles,0.5m cells over24x16x16m for180s, imposed1500C source20s; no trunks/buildings/embers. Six GAS outputs, no solid-ground temperature. Current model uses four geometry summaries, no explicit evolving fuel state; snapshot predictions not recurrence. Data are development, not pristine tests or physical validation. Existing particle material histories can support later state diagnostics, but that is not claimed by this phase.
''')
d={'stages':{'inputs':{'cmd':'../../.venv/bin/python setup_inputs.py','deps':['setup_inputs.py','../32_tree_expansion/development.json','../32_tree_expansion/groups.json','../32_tree_expansion/data/geometries.npz','../33_representation_loss/attempt14/results/coverage-summary.json'],'outs':[{'cases.json':{'cache':False}},{'groups.json':{'cache':False}},{'coverage-plan.json':{'cache':False}},'data/geometries.npz']},'package':{'cmd':'../../.venv/bin/python validate.py && ../../.venv/bin/python prepare_pilot.py','deps':[],'outs':['data/pilot-overlay.tar',{'results/input-freeze.json':{'cache':False}},{'results/preflight.json':{'cache':False}},{'gpu-workflow.yaml':{'cache':False}}]},'cloud_submit':{'cmd':'../../.venv/bin/python launch.py','deps':['launch.py','cloud.py','gpu-workflow.yaml','data/pilot-overlay.tar'],'metrics':[{'results/execution.json':{'cache':False}}]},'cloud_collect':{'cmd':'../../.venv/bin/python collect.py','deps':['collect.py','cloud.py','results/execution.json'],'outs':['data/collected'],'metrics':[{'results/cleanup.json':{'cache':False}},{'results/permission-removed.json':{'cache':False}}]},'analysis':{'cmd':'../../.venv/bin/python analyze.py','deps':['analyze.py','data/collected','coverage-plan.json'],'outs':['data/visuals'],'metrics':[{'results/analysis.json':{'cache':False}}]}}}
(a/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
print(a)
