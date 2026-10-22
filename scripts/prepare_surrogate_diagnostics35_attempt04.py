from pathlib import Path
import json,shutil,yaml
root=Path('/Users/wdavies/pi/wildfire3d'); parent=root/'experiments/35_surrogate_diagnostics'; old=parent/'attempt03'; a=parent/'attempt04';a.mkdir();(a/'data/resume').mkdir(parents=True);(a/'data/initial').mkdir();(a/'results').mkdir()
for p in old.glob('*.py'):
 s=p.read_text().replace('diag35-03','diag35-04').replace('gpu35-diag03','gpu35-diag04').replace('diagnostics35/attempt03','diagnostics35/attempt04');(a/p.name).write_text(s)
for n in ['cases.json','groups.json','replica-time-audit.json','input-sources.json','restore-manifest.json']:
 (a/n).write_text((old/n).read_text().replace('diagnostics35/attempt03','diagnostics35/attempt04'))
shutil.copy2(old/'data/geometries.npz',a/'data/geometries.npz');shutil.copy2(old/'data/collected/single-epoch-080.pt',a/'data/initial/single.pt')
plan=json.loads((old/'coverage-plan.json').read_text());plan['epochs']={'low':80,'restart':80};plan['scope']='Continuation of attempt03 single epoch80 from identical model and optimizer; one training trajectory, full32 development validation configurations each epoch. Same deterministic batch order for both arms. No pristine test.';plan['learning_rates']={'low':'constant 1e-5','restart':'cosine 3e-4 to1e-5 over80 additional epochs'};plan['schedule_seed_offset']=80;(a/'coverage-plan.json').write_text(json.dumps(plan,indent=2))
p=a/'worker.py';s=p.read_text();s=s.replace("base_state=copy.deepcopy(base.state_dict());del base", "base_state=copy.deepcopy(base.state_dict());del base\n initial_checkpoint=torch.load(R/'data/initial/single.pt',map_location='cuda',weights_only=False);assert initial_checkpoint['arm']=='single' and initial_checkpoint['epoch']==80 and initial_checkpoint['scales']==scales.tolist();base_state=copy.deepcopy(initial_checkpoint['model'])")
s=s.replace("for arm in ['source','single','eight','oracle']:","for arm in ['low','restart']:").replace("if arm=='single' else train","if arm in ['low','restart'] else train")
needle="sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=total_steps,eta_min=1e-5);history=[]"
replacement="""opt.load_state_dict(copy.deepcopy(initial_checkpoint['optimizer']))
  # Hash the common optimizer before the intentionally different rate/scheduler.
  statehash=hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for st in opt.state.values() for v in st.values() if torch.is_tensor(v))).hexdigest()
  upload(f'{arm}-initial-state.json',json.dumps(dict(model_sha256=digest(m),optimizer_tensor_sha256=statehash,source_epoch=80)).encode())
  rate=1e-5 if arm=='low' else 3e-4
  for group in opt.param_groups:group['lr']=rate;group['initial_lr']=rate
  sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=total_steps,eta_min=1e-5);history=[]"""
assert needle in s;s=s.replace(needle,replacement).replace('3501+epoch','3501+80+epoch');p.write_text(s)
p=a/'prepare_pilot.py';s=p.read_text().replace("+list((R/'data/resume').glob('*.pt'))","+list((R/'data/resume').glob('*.pt'))+list((R/'data/initial').glob('*.pt'))");p.write_text(s)
p=a/'analyze.py';s=p.read_text().replace("['source','single','eight','oracle']","['low','restart']").replace("arm!='single'","arm not in ['low','restart']").replace("Oracle uses true HRR at inference.","Matched single-trajectory learning-rate comparison from epoch80; additional epochs shown.");s=s.replace("for arm in ['low','restart']:","""states=[json.loads((R/'data/collected'/f'{arm}-initial-state.json').read_text()) for arm in ['low','restart']]
assert states[0]==states[1], 'Initial states differ'
initial_rows=[json.loads((R/'data/collected'/f'{arm}-epoch-000.json').read_text())['rows'] for arm in ['low','restart']]
assert initial_rows[0]==initial_rows[1], 'Initial metrics differ'
result['matched_initial_states']=states[0]
for arm in ['low','restart']:""");p.write_text(s)
p=a/'restore_inputs.py';p.write_text("""from pathlib import Path
import shutil
R=Path(__file__).parent
(R/'data/initial').mkdir(parents=True,exist_ok=True)
for n in ['cases.json','groups.json','data/geometries.npz']:shutil.copy2(R.parent/'attempt03'/n,R/n)
shutil.copy2(R.parent/'attempt03/data/collected/single-epoch-080.pt',R/'data/initial/single.pt')
""")
d=yaml.safe_load((old/'dvc.yaml').read_text());d['stages']['inputs']['deps']=['restore_inputs.py','../attempt03/cases.json','../attempt03/groups.json','../attempt03/data/geometries.npz','../attempt03/data/collected/single-epoch-080.pt'];d['stages']['inputs']['outs']=[{'cases.json':{'cache':False}},{'groups.json':{'cache':False}},'data/geometries.npz','data/initial/single.pt'];d['stages']['package']['deps']+=['data/initial/single.pt'];d['stages']['cloud_submit']=d['stages'].pop('recover_submission');d['stages']['cloud_submit']['cmd']='../../../.venv/bin/python launch.py';(a/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(a/'README.md').write_text('''# Experiment35 attempt04: single-trajectory optimization continuation

Compare constant learning rate1e-5 with cosine restart3e-4 to1e-5, each80 additional epochs, from identical attempt03 single epoch80 weights and optimizer. Same loss, training case x32_033_s0, normalization from original8TRAIN configurations, and shuffled nonoverlapping3-frame batch order (seed3501+80+epoch). Each epoch visits all91frames once. All32 development validation configurations40trajectories evaluated EVERYepoch. Not recurrence or a pristine test. No architecture or auxiliary-loss changes. Initial model/optimizer tensor hashes and initial full-history rows must match; learning-rate metadata intentionally differs after the shared restore. Resume preserves each arm's scheduler, RNG, schedule position and aggregate.

Question: did decay to a tiny learning rate prematurely stall fitting? A restart improving fit supports an optimization explanation; failure to improve does not prove a capacity limit. Prespecified training normalized MAE target0.05 remains distinct from physical fidelity. Report all physical outputs and late curves, not just aggregate loss.

Fully reserve4.50USD before upload/compute: cumulative88.10 of100 including prior failures/archive, invoice unknown. No laptop training/newFDS. Estimated40–70minutes;90min task,95minVM,120minabsolute,20minqueue limits. Checkpoint each epoch/every250updates; preserve interruption evidence. No blind retries. Fresh SHAverified copies of all48existing trajectories avoid bucket age1expiry; policy unchanged. Collector verifies job/VM/disks empty and removes exact temporary read grant.

Simulation scope: generic3mwide conical crowns4/6/8/10m above2m,1600weightedparticles,0.5m24x16x16m domain180s, artificial1500C20s source; no trunks/buildings/embers. Six gasfields, not solid ground temperature. Snapshot model uses geometry summaries, not evolving fuel state. No physical validation claim.
''')
shutil.copy2('/tmp/make35_04.py',root/'scripts/prepare_surrogate_diagnostics35_attempt04.py')
