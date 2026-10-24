"""Prepare the diagnosed memory-comparison continuation; never submit compute."""
from pathlib import Path
import json,yaml
repo=Path(__file__).resolve().parents[1];old=repo/'experiments/35_surrogate_diagnostics/attempt16';r=old.parent/'attempt17';r.mkdir(exist_ok=False);(r/'data').mkdir();(r/'results').mkdir()
for name in ['model.py','worker.py','validate.py','cloud.py','collect.py','prepare_pilot.py','finish_run.py','finalize_archive.py','analyze.py','launch.py']:
 s=(old/name).read_text().replace('attempt16','attempt17').replace('memory35-16','memory35-17').replace('gpu35-memory16','gpu35-memory17').replace('exp35-memory16','exp35-memory17')
 if name=='finalize_archive.py':
  s=s.replace("  if (R/'results/collection-error.json').exists() and not (R/'results/collected.json').exists():\n   from archive_partial import main as preserve_partial\n   preserve_partial();return\n",'')
 if name=='launch.py':
  s=s.replace('+6<=','+3<=').replace('+6,2)','+3,2)').replace('allowance_usd=6','allowance_usd=3').replace('compute_allowance_usd=4.4','compute_allowance_usd=2.2').replace('ancillary_cleanup_allowance_usd=1.6','ancillary_cleanup_allowance_usd=.8').replace('expected_usd=[2,4.5]','expected_usd=[.5,1.5]')
  s=s.replace("clauses=['resource.name == '+json.dumps(base+'diagnostics35/attempt17/pilot-overlay.tar')]", "clauses=['resource.name.startsWith('+json.dumps(base+'diagnostics35/attempt17/')+')']")
  s=s.replace('24h exact verified 520-history minimal-material sequence package only','24h read for this new attempt input and output prefix only; enables immutable-upload verification')
 if name=='prepare_pilot.py':
  s=s.replace("'+ 23400'","'+ 12600'").replace("'+ 21900'","'+ 11100'").replace("'21600s'","'10800s'").replace('proposed_new_cap_usd=6','proposed_new_cap_usd=3').replace('estimated_usd=[2,4.5]','estimated_usd=[.5,1.5]').replace('task_deadline_s=21600','task_deadline_s=10800').replace('vm_age_limit_s=21900','vm_age_limit_s=11100').replace('absolute_deadline_s=23400','absolute_deadline_s=12600')
 (r/name).write_text(s)
p=json.loads((old/'coverage-plan.json').read_text());p['continuation']={'source':'../attempt16','reason':'HTTP503 upload then recoverymetadata403; not scientific failure','completed_jobs_skipped':list(range(15)),'resume_job':15,'resume_epoch':373,'remaining_jobs':[16,17,18,19],'science_unchanged':True};p['budget']=dict(expected_usd=[.5,1.5],maximum_allowance_usd=3,task_seconds=10800,vm_seconds=11100,absolute_seconds=12600,soft_seconds=9900,queue_seconds=1200);(r/'coverage-plan.json').write_text(json.dumps(p,indent=2))
(r/'prepare.py').write_text('''"""Copy only SHA256-verified preserved inputs and resume states. No optimization."""
from pathlib import Path
import json,shutil,hashlib,torch
R=Path(__file__).resolve().parent;old=R.parent/'attempt16';dest=R/'data/resume';dest.mkdir(parents=True,exist_ok=True);(R/'results').mkdir(exist_ok=True)
inv=json.loads((old/'results/partial-inventory.json').read_text())['files'];proof={}
for name in ['schema.json','data/sequences.npz']:shutil.copyfile(old/name,R/name)
for k in range(15):
 for suffix in ['-report.json','-selected.pt']:
  name=f'fold{k:02}'+suffix;p=old/'data/collected'/name;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==inv[name]['sha256'];shutil.copyfile(p,dest/name);proof[name]=h
name='fold15-epoch373.pt';p=old/'data/collected'/name;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==inv[name]['sha256'];shutil.copyfile(p,dest/'fold15.pt');proof['fold15.pt']=h
c=torch.load(dest/'fold15.pt',map_location='cpu',weights_only=False);assert c['fold']==15 and c['epoch']==373 and c['kind']=='gru';assert c['schema_hash']==hashlib.sha256((R/'schema.json').read_bytes()).hexdigest();assert c['history'][-1]['epoch']==373
assert all(k in c for k in ['optimizer','rng','best_state','best_epoch','globalstep'])
assert not (old/'data/collected/selection-freeze.json').exists();assert not list((old/'data/collected').glob('*-test.json'))
(R/'results/resume-proof.json').write_text(json.dumps(dict(source=str(old),files=proof,model15_epoch=373,completed_models=15,optimizer_rng_selection_preserved=True,test_not_started=True,local_training=False),indent=2))
''')
d=yaml.safe_load((old/'dvc.yaml').read_text());d['stages']['prepare_data']={'cmd':'../../../.venv/bin/python prepare.py','deps':['prepare.py','../attempt16/data/sequences.npz','../attempt16/schema.json','../attempt16/data/collected','../attempt16/results/partial-inventory.json'],'outs':['data/sequences.npz','data/resume',{'schema.json':{'cache':False}}],'metrics':[{'results/resume-proof.json':{'cache':False}}]};d['stages']['package']['deps']+=['data/resume','results/resume-proof.json','validate_transport.py'];d['stages']['package']['cmd']='../../../.venv/bin/python validate.py && ../../../.venv/bin/python validate_transport.py && ../../../.venv/bin/python prepare_pilot.py';d['stages']['package']['metrics']=[{'results/transport-preflight.json':{'cache':False}}];(r/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(r/'README.md').write_text('''# Diagnosed continuation of the matched MLP/GRU comparison — attempt17

Prepared only; user approval required before launch. This continues attempt16 with unchanged models, inputs, folds, losses, schedules, seeds and validation/test selection. No fresh scientific sweep. Skip15 completed jobs, resume GRU rotation7 (job15) after epoch373 with its optimizer, RNG, history and selection state; finish jobs16–19. All20selected models freeze before any test. Parent failure occurred during checkpoint upload HTTP503; the metadata check then got403 because output reads were not permitted. Training did not report a mathematical failure. Parent raw/source/checkpoints remain immutable and archived.

Only transport/permissions and run identity/deadlines change. New attempt17 prefix receives narrow24h objectViewer access including its input and its outputs, permitting unknown-upload verification. Create-only uploads never overwrite. Bounded backoff retries transient upload and metadata failures; 403 is fatal, different content is fatal. No automatic paid retry. A startup probe verifies create/read metadata/exact byte digest and idempotent replay before any training. All supplied resume files checked against parent SHA256 inventory and original schema hash. Local preflight uses no optimizer.

Full520 histories480configs, same10grouped8/1/1rotations. Three evolving physical states ONLY: derived remaining water kg, unreacted dry vegetation kg, vegetation fuel-gas release kg/s—not heat. Char inert ash. Both receive21 measured inputs (four3-state history plus9forcing/static); MLP5763params versus GRU5379 with32internal latent memory. Same1/8/16/32step curriculum, min100max400patience30, train/validation everyepoch; all20selectionsbeforetests. No new data, architecture, clipping or auxiliary loss. Prefix memory teacher-forced under no_grad; self-fed gradient within training window. Full180s rollout has no futuretruth. Report one-step and2/8/16/32/90s horizons against no-change, active/quiet, negative/mass-increase magnitudes. Previously examined reshuffleddata notpristine.

Expectedadditionalcompute$0.50–1.50,maximumallowance$3includingancillary/cleanup. Three-hourtask,3h05VM,3h30absolute,2h45soft,20minqueue. Checkpoint eachcompletedepoch; no silent restart. Measuredruntime replaces allowance, matchingpostedbilling laterreplacesestimate. No localtraining/newFDS. Preservealloutputs DVC/publicapprovedHF andcode/workflowgeneratorGitHub. Collector verifiesVMjobdisks empty/removesexacttemporarygrant. Generic3mwidecones4/6/8/10mabove2m1600particles,.5m24x16x16m180s1500C20ssource,no trunks/buildings/embers;48legacygeometrydocumented. Derivedyield.75andwaterintegration, noheat/plume/physicalvalidation.
''')
print(r)
