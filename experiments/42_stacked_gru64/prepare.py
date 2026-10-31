from pathlib import Path
import shutil,json,ast
R=Path(__file__).resolve().parent;S=R.parent/'41_dropout10_from_start/data/training';D=R/'data/training'
assert not (R/'results/submission-intent.json').exists()
D.mkdir(parents=True,exist_ok=True)
for name in ['model.py','plain_model.py','objective.py','runtime.py','schema.json','data/sequences.npz']:
 target=D/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/name,target)
for name in ['worker.py','gated_model.py']:shutil.copy2(R/name,D/name)
p=json.loads((S/'coverage-plan.json').read_text());assert 'continuation' not in p
p.update(experiment='42 fresh rotation0: two recurrent GRU64 layers, no dropout',architecture='GRU41->64 then GRU64->64; shared Linear64->64 + SiLU; four delta and three sigmoid gate heads;50119 parameters',recurrent_layers=2,dropout_probability=0,dropout_scope='No dropout anywhere',initialization='Fresh seed3516 model and empty AdamW; no inherited weights, optimizer or epochs',burn_in='Both GRU states initialized zero; both teacher-prefix states recomputed under no_grad through the window origin only; gradients within window. Autonomous evaluation uses predicted states.')
(D/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
assert not (D/'data/resume').exists()
for f in D.glob('*.py'):ast.parse(f.read_text())
