"""Prepare a diagnosed RNG-restore correction only; never submits compute."""
from pathlib import Path
import json,yaml
repo=Path(__file__).resolve().parents[1];old=repo/'experiments/35_surrogate_diagnostics/attempt17';r=old.parent/'attempt18';r.mkdir(exist_ok=False);(r/'data').mkdir();(r/'results').mkdir()
for name in ['model.py','worker.py','validate.py','validate_transport.py','cloud.py','runtime.py','collect.py','prepare_pilot.py','finish_run.py','finalize_archive.py','analyze.py','launch.py','prepare.py','coverage-plan.json','dvc.yaml','README.md']:
 s=(old/name).read_text().replace('attempt17','attempt18').replace('memory35-17','memory35-18').replace('gpu35-memory17','gpu35-memory18').replace('exp35-memory17','exp35-memory18')
 (r/name).write_text(s)
p=r/'worker.py';s=p.read_text().replace("torch.cuda.set_rng_state_all(x['cuda'])", "torch.cuda.set_rng_state_all([state.cpu() for state in x['cuda']])")
pos=s.index('reports=[]')
s=s[:pos]+'''# Exercise the actual saved checkpoint on the actual GPU before any fitting.
resume_probe=R/'data/resume/fold15.pt'
if resume_probe.exists():
 c=torch.load(resume_probe,map_location=device,weights_only=False);probe_model=Transition(c['kind']).to(device);probe_model.load_state_dict(c['model']);probe_opt=torch.optim.AdamW(probe_model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);probe_opt.load_state_dict(c['optimizer'])
 restore_rng(c['rng']);cpu_draw=torch.rand(8);gpu_draw=torch.rand(8,device=device);np_draw=np.random.random(8);py_draw=random.random()
 restore_rng(c['rng']);assert torch.equal(cpu_draw,torch.rand(8));assert torch.equal(gpu_draw,torch.rand(8,device=device));assert np.array_equal(np_draw,np.random.random(8));assert py_draw==random.random();restore_rng(c['rng'])
 x=torch.zeros(4,4,3,device=device);u=external[:4,0];y=probe_model(x,u);buf=io.BytesIO();torch.save(probe_model.state_dict(),buf);buf.seek(0);probe_model2=Transition(c['kind']).to(device);probe_model2.load_state_dict(torch.load(buf,map_location=device,weights_only=False));assert torch.equal(y,probe_model2(x,u))
 save('resume-cloud-check.json',dict(passed=True,checkpoint_epoch=c['epoch'],cpu_rng_replay=True,cuda_rng_replay=True,numpy_rng_replay=True,python_rng_replay=True,optimizer_loaded=True,saved_model_forward_replay=True,optimization_performed=False))
 del probe_model,probe_model2,probe_opt,c
'''+s[pos:];p.write_text(s)
p=r/'coverage-plan.json';x=json.loads(p.read_text());x['continuation']['additional_repair']='Saved CUDA RNG states explicitly moved to CPU for restore; actual checkpoint GPU RNG/model/optimizer replay preflight required. Attempt17 did not resume training.';p.write_text(json.dumps(x,indent=2))
p=r/'dvc.yaml';x=yaml.safe_load(p.read_text());x['stages']['package']['deps'].append('validate_resume.py');x['stages']['package']['cmd']='../../../.venv/bin/python validate.py && ../../../.venv/bin/python validate_transport.py && ../../../.venv/bin/python validate_resume.py && ../../../.venv/bin/python prepare_pilot.py';x['stages']['package']['metrics'].append({'results/resume-preflight.json':{'cache':False}});p.write_text(yaml.safe_dump(x,sort_keys=False))
p=r/'launch.py';s=p.read_text().replace("  assert read('results/transport-preflight.json')['passed']", "  assert read('results/transport-preflight.json')['passed']\n  assert read('results/resume-preflight.json')['passed']");p.write_text(s)
p=r/'README.md';s=p.read_text();s=s.replace('User explicitly approved the continuation with a $3 maximum allowance. First submission succeeded on 2026-10-24; execution01ae861d-6d4c-4884-8ae1-85cc5824d2c7.','Prepared only. Separate approval required before launch. Attempt17 stopped before training because torch.load(map_location=cuda) moved RNG ByteTensors onto GPU; CUDA generator restore requires CPU tensors. This attempt converts those saved states to CPU and adds real saved-checkpoint CPU/CUDA/NumPy/Python RNG replay plus optimizer/model restore checks on GPU before fitting. No scientific change.');p.write_text(s)
print(r)
