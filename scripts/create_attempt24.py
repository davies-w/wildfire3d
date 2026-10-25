"""Generate corrected gated comparison without launching or modifying attempt23."""
from pathlib import Path
import yaml
repo=Path(__file__).resolve().parents[1];old=repo/'experiments/35_surrogate_diagnostics/attempt23';r=old.parent/'attempt24'
r.mkdir(exist_ok=False);(r/'data/resume').mkdir(parents=True);(r/'results').mkdir()
for p in old.iterdir():
 if p.suffix=='.py' or p.name in ['coverage-plan.json','README.md','dvc.yaml']:
  s=p.read_text().replace('attempt23','attempt24').replace('gates23','gates24').replace('gates35-23','gates35-24')
  (r/p.name).write_text(s)
(r/'data/.gitignore').write_text('/collector.lock\n/finish.lock\n/archive.lock\n/archive-sync-plan.jsonl\n')
p=r/'worker.py';s=p.read_text();needle='torch.cumsum((positive[:,1:]+positive[:,:-1])*.5*dt[ids],1)';assert s.count(needle)==1
s=s.replace(needle,'torch.cumsum(((positive[:,1:]+positive[:,:-1])*.5*dt[ids]).cpu(),1).to(device)')
needle="save('cuda-check.json',dict(passed=True,checks=checks))"
extra='''# Exercise the complete reporting path for both arms before any optimizer/fitting.
evaluation_checks=[]
for check_kind in P['arms']:
 ids=torch.tensor(meta['rotations'][0]['validation'],device=device)
 train_ids=torch.tensor(meta['rotations'][0]['train'],device=device)
 cm,cs=normalize_fit(raw,train_ids,config,scale);cz=(torch.asinh(raw/scale)-cm)/cs
 check_model=Transition(check_kind).to(device);check_model.set_normalization(cm,cs)
 result=evaluate(check_model,cz,ids,cm,cs,True)
 assert all(result[mode]['finite'] for mode in ['one_step','rollout'])
 evaluation_checks.append(dict(kind=check_kind,passed=True,modes=list(result)))
save('evaluation-cloud-check.json',dict(passed=True,checks=evaluation_checks))
'''
s=s.replace(needle,needle+'\n'+extra);p.write_text(s)
(r/'validate_evaluation.py').write_text('''"""Execute actual evaluation definitions on CPU, without optimizer or fitting."""
from pathlib import Path
import ast,json
R=Path(__file__).resolve().parent
source=(R/'worker.py').read_text().split('checks=[]')[0]
source=source.replace("assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'",'').replace("device='cuda'","device='cpu'")
assert 'optimizer' not in source
ns={'__file__':str(R/'worker.py')};exec(compile(source,str(R/'worker.py'),'exec'),ns)
torch=ns['torch'];ids=torch.tensor(ns['meta']['rotations'][0]['validation']);train=torch.tensor(ns['meta']['rotations'][0]['train'])
mean,std=ns['normalize_fit'](ns['raw'],train,ns['config'],ns['scale']);z=(torch.asinh(ns['raw']/ns['scale'])-mean)/std
checks=[]
for kind in ns['P']['arms']:
 model=ns['Transition'](kind);model.set_normalization(mean,std)
 a=ns['evaluate'](model,z,ids,mean,std,True);b=ns['evaluate'](model,z,ids,mean,std,True)
 assert a==b
 assert all(a[k]['finite'] for k in ['one_step','rollout'])
 checks.append(dict(kind=kind,passed=True,exact_replay=True))
(R/'results/evaluation-preflight.json').write_text(json.dumps(dict(passed=True,checks=checks,no_optimizer=True),indent=2));print(checks)
''')
p=r/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['package']['cmd']=d['stages']['package']['cmd'].replace('&& ../../../.venv/bin/python prepare_pilot.py','&& ../../../.venv/bin/python validate_evaluation.py && ../../../.venv/bin/python prepare_pilot.py');assert 'validate_evaluation.py &&' in d['stages']['package']['cmd'];d['stages']['package']['deps'].append('validate_evaluation.py');d['stages']['package']['metrics'].append({'results/evaluation-preflight.json':{'cache':False}});p.write_text(yaml.safe_dump(d,sort_keys=False))
p=r/'launch.py';s=p.read_text().replace("assert read('results/preflight.json')['passed']","assert read('results/preflight.json')['passed']\n  assert read('results/evaluation-preflight.json')['passed']");p.write_text(s)
p=r/'README.md';p.write_text(p.read_text()+'\n## Corrected startup reporting\nAttempt23 stopped before fitting because CUDA cumulative sum is unsupported under strict determinism. This attempt moves only the detached reporting cumulative sum to CPU, returning its result to GPU. Training, losses, scorecard and data remain unchanged. Full initial evaluation of both arms is now mandatory locally without optimization and on GPU before fitting. User explicitly approved fixing and continuing after failure. Prior run cost approximately $0.03474; this new attempt retains the $8 maximum allowance.\n')
