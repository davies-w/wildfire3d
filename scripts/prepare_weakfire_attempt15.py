from pathlib import Path
import shutil,json
import yaml
r=Path(__file__).resolve().parents[1]/'experiments/33_representation_loss';a=r/'attempt15';a.mkdir(exist_ok=False);(a/'data/resume').mkdir(parents=True);(a/'results').mkdir()
for p in (r/'attempt14').glob('*.py'):
 if p.name not in ['resume_submission.py','analyze_coverage.py','diagnose_strength.py']: (a/p.name).write_text(p.read_text().replace('pilot14','pilot15'))
shutil.copy2(r/'attempt14/data/initial_snapshot.pt',a/'data/initial_snapshot.pt')
(a/'restore_inputs.py').write_text("from pathlib import Path\nimport shutil\nr=Path(__file__).parent\n(r/'data/resume').mkdir(parents=True,exist_ok=True)\nshutil.copy2(r/'../attempt14/data/collected/expand360-checkpoint-12000.pt',r/'data/resume/current.pt')\n")
(a/'setup_coverage.py').write_text('''"""Fixed strength-stratified TRAIN subset; no validation target selection."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;S=R.parent.parent/'32_tree_expansion'
cs=json.loads((S/'development.json').read_text());metrics=json.loads((R.parent/'attempt14/results/coverage-summary.json').read_text())['configuration_metrics']
mm={x['configuration']:x['metrics']['truth_mean_HRR_kW'] for x in metrics if x['arm']=='expand360' and x['stage']=='final' and x['cohort']=='all_train360' and x['window']=='post_source'}
rng=np.random.default_rng(3315);names=[]
for lo,hi in [(0,1),(1,10),(10,100),(100,float('inf'))]:
 pool=sorted(n for n,v in mm.items() if lo<=v<hi);names+=list(rng.choice(pool,12,replace=False))
train=[c for c in cs if c['split']=='train' and c['new_geometry'] and c['replica']==0 and c['configuration'] in names];val=[c for c in cs if c['split']=='validation' and c['new_geometry']];chosen=train+val
assert len(train)==48 and len(val)==40
(R/'cases.json').write_text(json.dumps(chosen,indent=2));case_names={c['case'] for c in chosen};groups=json.loads((S/'groups.json').read_text());(R/'groups.json').write_text(json.dumps([g for g in groups if case_names.intersection(g['cases'])],indent=2));z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in case_names})
(R/'coverage-plan.json').write_text(json.dumps(dict(train_configurations=sorted(names),validation_configurations=sorted({c['configuration'] for c in val}),animation_cases=['x32_360_s0','x32_368_s0','x32_376_s0','x32_384_s0'],scope='48 strength-stratified training configurations,12 each truth-HRR band <1/1-10/10-100/>=100kW;32 existing development validation configs40trajectories. Same4000updates/schedule/initial14expanded model and optimizer; physical_low control versus added absolute total-HRR error/(truth+10kW) weights.02/.1. No pristine test.'),indent=2))
''')
(a/'physical_background_losses.py').write_text((a/'matched_losses.py').read_text())
(a/'matched_losses.py').write_text('''"""Physical total heat-release error reduces absolute false burning in weak frames."""
from physical_background_losses import objective_for as baseline
from previous_loss import quantities

def strength_term(p,y):
 _,q,_=quantities(p);_,target,_=quantities(y)
 total=q.sum((1,2,3))*.125;truth=target.sum((1,2,3))*.125
 return ((total-truth).abs()/(truth+10)).mean()

def objective_for(arm,p,y,ambient):
 loss=baseline('physical_low',p,y,ambient)
 return loss+{'control':0.,'strength_low':.02,'strength_high':.1}[arm]*strength_term(p,y)
''')
s=(a/'worker.py').read_text().replace("saved['step']==6000","saved['step']==12000").replace("['continue120','expand360']","['control','strength_low','strength_high']")
s=s.replace("pool=train if arm=='expand360' else [c for c in train if c['configuration'] in json.loads((R/'coverage-plan.json').read_text())['reference_configurations']]","pool=train")
s=s.replace('range(12000)','range(4000)').replace('11999','3999').replace("objective_for('physical_low',p,y,ambient)","objective_for(arm,p,y,ambient)")
s=s.replace('rows=[];reports={};started=',"rows=[];reports={};projections={};plan=json.loads((R/'coverage-plan.json').read_text());started=")
s=s.replace("out.append(dict(arm=arm,stage=tag,case=c['case'],split=c['split'],configuration=c['configuration'],replica=c['replica'],**metrics(np.array(a),decode(np.concatenate(pp),c['wind_speed']),t)))", "truth=np.array(a);b=decode(np.concatenate(pp),c['wind_speed']);out.append(dict(arm=arm,stage=tag,case=c['case'],split=c['split'],configuration=c['configuration'],replica=c['replica'],**metrics(truth,b,t)))\n    if c['case'] in plan['animation_cases']:\n     projections[c['case']+'_'+(arm if tag=='final' else 'initial')]=b[:,[0,1]].max(axis=3);projections[c['case']+'_FDS']=truth[:,[0,1]].max(axis=3);projections[c['case']+'_time']=t")
s=s.replace(" raw=json.dumps(dict(final_weights", " buf=io.BytesIO();np.savez_compressed(buf,**projections);upload('projections.npz',buf.getvalue())\n raw=json.dumps(dict(final_weights")
s=s.replace("scope='Fixed physical_low loss; same saved pilot13expanded1206000 weights/optimizer and12000additionalupdates. Continue120 vs expand360 trainingconfigs,32valconfigs40trajectories. Same update budget, not equal epochs; no pristine test.'","scope=plan['scope']")
(a/'worker.py').write_text(s)
s=(a/'validate.py').read_text().replace("['control','dose_background','physical_low','dose_repeat']","['control','strength_low','strength_high']").replace('==392','==80');(a/'validate.py').write_text(s)
s=(a/'prepare_pilot.py').read_text().replace("'+ 7200'","'+ 5400'").replace("'+ 5700'","'+ 3900'").replace("'5400s'","'3600s'").replace("='100'","='60'").replace('proposed_new_cap_usd=4.5','proposed_new_cap_usd=3.0').replace('task_deadline_s=5400','task_deadline_s=3600').replace('vm_age_limit_s=5700','vm_age_limit_s=3900').replace('absolute_deadline_s=7200','absolute_deadline_s=5400');(a/'prepare_pilot.py').write_text(s)
s=(a/'collect.py').read_text().replace("  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/repair33/pilot15/error.txt'", "  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/repair33/pilot15/projections.npz',str(dest)],check=False)\n  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/repair33/pilot15/error.txt'");(a/'collect.py').write_text(s)
s=(a/'launch.py').read_text().replace('+4.5','+3.0').replace('allowance_usd=4.5','allowance_usd=3.0').replace('compute_allowance_usd=1.6','compute_allowance_usd=1.2').replace('ancillary_cleanup_allowance_usd=2.9','ancillary_cleanup_allowance_usd=1.8')
start=s.index("  base='projects/_/buckets/'");end=s.index('  subprocess.run([G,\'storage\',\'buckets\',\'add-iam',start)
s=s[:start]+'''  base='projects/_/buckets/'+BUCKET+'/objects/'
  allgroups=json.loads((R.parent.parent/'32_tree_expansion/groups.json').read_text());allcases={c['case']:c for c in json.loads((R.parent.parent/'32_tree_expansion/cases.json').read_text())}
  prefixes=['expansion32/x32-development-','expansion32/x32-coverage-00-r1/']
  allowed=[g for g in allgroups if any(('expansion32/'+g['id']+'/').startswith(p) for p in prefixes)]
  assert all(allcases[n]['split']!='test' for g in allowed for n in g['cases'])
  assert {g['id'] for g in read('groups.json')} <= {g['id'] for g in allowed}
  clauses=['resource.name == '+json.dumps(base+'repair33/pilot15/pilot-overlay.tar')]+['resource.name.startsWith('+json.dumps(base+p)+')' for p in prefixes]
  condition=dict(title='exp33-pilot15-development-inputs',description='24h development-only prefixes; group members verified non-test',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
'''+s[end:];(a/'launch.py').write_text(s)
d=yaml.safe_load((r/'attempt14/dvc.yaml').read_text());d['stages'].pop('recover_submission');d['stages'].pop('coverage_analysis');d['stages'].pop('strength_diagnosis');d['stages']['resume_inputs']['deps']=['restore_inputs.py','../attempt14/data/collected/expand360-checkpoint-12000.pt'];d['stages']['coverage_inputs']['deps']=['setup_coverage.py','../attempt14/results/coverage-summary.json','../../32_tree_expansion/development.json','../../32_tree_expansion/groups.json','../../32_tree_expansion/data/geometries.npz'];d['stages']['package']['deps']+=['physical_background_losses.py','previous_loss.py'];(a/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(a/'README.md').write_text('''# Matched physical heat-release loss diagnostic\n\n48 training configs:12 randomly selected within each truth post-source mean-HRR band <1,1–10,10–100,>=100kW. Selection uses TRAIN truths only. Same prior expanded360 checkpoint/optimizer, same4000-update schedule, physical_low baseline; extra total-HRR absolute error/(truth+10kW), weights0/.02/.1. This floor avoids unbounded weighting of near-zero references; not a claim of calibrated accuracy. Uniform cases on this stratified subset oversamples weak fires in every arm, including control.32 prior development validation configs40trajectories, no pristine test. Check all heat/temperature/radiation/velocity/weak/strong tradeoffs.\n\nFour previously selected height-based animation cases retained, max-y gas-temperature/HRR projections with common scales, not flame geometry. Allarms warmstart; three-frame loss not recurrence. Generic3mwide cones4/6/8/10mabove2m1600particles,.5m24x16x16m180s1500C20s artificialsource,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature. No physicalvalidation.\n\nReserve3USD fully before submission, cumulative cap75; expected25–45min including88case preprocessing;20minqueue/60mintask/65minVM/90minabsolute;500step uploaded checkpoints, separately reserved recovery only. No laptoptraining/newFDS.24h temporary read development-only prefixes verifiednon-test, removed by lockedcollector.\n''')
print(a)
