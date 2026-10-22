"""Prepare immutable checkpoint evaluation, never retrain or select by validation score."""
from pathlib import Path
import json,shutil,hashlib,yaml
import numpy as np
R=Path(__file__).resolve().parents[1]/'experiments/33_representation_loss';A=R/'attempt16';A.mkdir(exist_ok=False);(A/'results').mkdir();(A/'data/resume').mkdir(parents=True)
for p in (R/'attempt15').glob('*.py'):
 if p.name not in ['worker.py','validate.py','analyze.py','render_projections.py','setup_coverage.py','restore_inputs.py']:(A/p.name).write_text(p.read_text().replace('pilot15','pilot16'))
(A/'.gitignore').write_text('/data/\n/__pycache__/\n')
cs=json.loads((R/'attempt15/cases.json').read_text());rows=json.loads((R/'attempt15/results/comparison.json').read_text())['configurations'];truth={x['configuration']:x['metrics']['truth_mean_HRR_kW'] for x in rows if x['arm']=='control' and x['stage']=='initial' and x['split']=='train' and x['window']=='post_source'}
rng=np.random.default_rng(3316);names=[]
for lo,hi in [(0,1),(1,10),(10,100),(100,float('inf'))]:names+=list(rng.choice(sorted(n for n,v in truth.items() if lo<=v<hi),3,replace=False))
chosen=[c for c in cs if c['split']=='validation' or c['configuration'] in names];assert len(chosen)==52
(A/'cases.json').write_text(json.dumps(chosen,indent=2));groups=json.loads((R/'attempt15/groups.json').read_text());ids={c['case'] for c in chosen};(A/'groups.json').write_text(json.dumps([g for g in groups if ids.intersection(g['cases'])],indent=2));z=np.load(R/'attempt15/data/geometries.npz');np.savez_compressed(A/'data/geometries.npz',**{n:z[n] for n in ids})
models=[]
def add(arm,step,src,pool,loss_arm):
 name=f'{arm}-{step:05}.pt';shutil.copy2(src,A/'data/resume'/name);models.append(dict(arm=arm,step=step,file=name,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),training_configurations=pool,loss_arm=loss_arm,source=str(src.relative_to(R))))
add('coverage360',0,R/'attempt14/data/resume/current.pt',360,'control')
for s in range(500,12001,500):add('coverage360',s,R/f'attempt14/data/collected/expand360-checkpoint-{s}.pt',360,'control')
for arm in ['control','strength_low','strength_high']:
 add(arm,0,R/'attempt15/data/resume/current.pt',48,arm)
 for s in range(500,4001,500):add(arm,s,R/f'attempt15/data/collected/{arm}-checkpoint-{s}.pt',48,arm)
(A/'coverage-plan.json').write_text(json.dumps(dict(models=models,training_panel_configurations=sorted(names),cases=sorted(ids),scope='Checkpoint evaluation only, no optimizer. All saved500-step checkpoints for14expand360 and15three arms, each with its true starting weights. Fixed12trainingconfigs (3perTRAIN truth strength band) and all32validationconfigs40trajectories. Full180s histories and identical per-model objective evaluation. Training panel is stratified subset, not full training-set loss. Prior development validation, not pristine test. Updates/configuration is expected sampling passes, not epochs under replacement.'),indent=2))
shutil.copy2(R/'attempt15/data/initial_snapshot.pt',A/'data/initial_snapshot.pt')
s=(A/'prepare_pilot.py').read_text().replace("'+ 5400'","'+ 7200'").replace("'+ 3900'","'+ 5700'").replace("'3600s'","'5400s'").replace('proposed_new_cap_usd=3.0','proposed_new_cap_usd=4.5').replace('task_deadline_s=3600','task_deadline_s=5400').replace('vm_age_limit_s=3900','vm_age_limit_s=5700').replace('absolute_deadline_s=5400','absolute_deadline_s=7200');(A/'prepare_pilot.py').write_text(s)
s=(A/'launch.py').read_text().replace('+3.0','+4.5').replace('allowance_usd=3.0','allowance_usd=4.5').replace('compute_allowance_usd=1.2','compute_allowance_usd=1.6').replace('ancillary_cleanup_allowance_usd=1.8','ancillary_cleanup_allowance_usd=2.9');(A/'launch.py').write_text(s)
d=yaml.safe_load((R/'attempt15/dvc.yaml').read_text());d['stages']={k:v for k,v in d['stages'].items() if k in ['package','cloud_submit','cloud_collect']};(A/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(A/'README.md').write_text('''# Did training run long enough? Saved-checkpoint learning curves\n\nEvaluation only, no retraining and no best-model selection. Evaluate all500-step checkpoints for14expand360 (0–12000) and15control/strength_low/strength_high (0–4000),52models including shared starts. Fixed12trainingconfigs (3per training-strength band) and all32validationconfigs/40trajectories;52cases per model, full180s histories. Training curve is a deliberately stratified panel, not all360/48trainingconfigs. Plot all output errors and weak/strong strata against updates and expected sampling passes (sampling with replacement, not conventional epochs). Compare late trajectories to distinguish continued fit, overfit, and plateau; no claim saturation from endpoints alone. Record mean fixed-panel full-history loss, not historical minibatch average, which cannot be recovered.\n\nReserve4.50USD before submission; cumulative70.10/75. Expected60–85minutes including decoding and CPU metrics;90mintask95minVM120minabsolute20minqueue. Upload per-model results immediately; partial results preserved if interrupted, separately reserved evaluation-only continuation required. Existing development-only temporary input grants removed by collector. No laptoptraining/newFDS. Generic3mwidecones4/6/8/10mabove2m1600particles,.5m24x16x16m180s artificial1500C20s source,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature;no pristine test/physicalvalidation.\n''')
print(A,len(models),len(chosen))
