from pathlib import Path
import shutil,json,ast
R=Path(__file__).resolve().parent;S=R.parent/'40_dropout10_continuation/data/training02';D=R/'data/training'
assert not (R/'results/submission-intent.json').exists()
D.mkdir(parents=True,exist_ok=True)
for name in ['model.py','plain_model.py','gated_model.py','objective.py','runtime.py','schema.json','data/sequences.npz']:
 target=D/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/name,target)
shutil.copy2(R/'worker.py',D/'worker.py')
p=json.loads((S/'coverage-plan.json').read_text());p.pop('continuation');p['experiment']='41 fresh rotation0: shared SiLU dropout10% from epoch1';p['minimum_epochs']=160;p['horizon_curriculum']=p['horizon_curriculum'][:-1];p['architecture']='GRU41->64; shared Linear64->64 + SiLU + Dropout0.1; four delta and three sigmoid gate heads;25159 parameters';p['initialization']='Fresh seed3516 model and empty AdamW; no inherited weights, optimizer or epochs';p['dropout_scope']='After shared SiLU from epoch1; both heads; evaluation off; no recurrent dropout'
(D/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
assert not (D/'data/resume').exists()
for f in D.glob('*.py'):ast.parse(f.read_text())
