from pathlib import Path
import json,shutil,ast
R=Path(__file__).resolve().parent;S=R.parent/'41_dropout10_from_start/data/training';D=R/'data/training';D.mkdir(exist_ok=True);assert not (R/'results/submission-intent.json').exists()
for name in ['objective.py','runtime.py','schema.json','data/sequences.npz']:
 p=D/name;p.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(S/name,p)
for name in ['model.py','gated_model.py','worker.py','joint_objective.py']:shutil.copy2(R/name,D/name)
shutil.copy2(R/'data/labels/cones.npz',D/'data/cones.npz')
p=json.loads((S/'coverage-plan.json').read_text());p.update(experiment='45 fresh single-GRU four-state plus cone multitask',architecture='GRU41->64; shared Linear64+SiLU; four deltas, three gates, six cone outputs;25549 trainable parameters',dropout_probability=0.,dropout_scope='No dropout',cone_parameter_weight=1.,cone_presence_weight=.1,cone_huber_beta=.1,cone_scales=[12.,90.,24.,16.,1500.],selection='Full-rollout validation: four-state integral + 1.0 cone parameter SmoothL1(beta=.1) + 0.1 cone presence BCE; auxiliary old gate BCE excluded from selection',initialization='Fresh seed3516 and EMPTY optimizer; no inherited checkpoint or epochs',cone_scope='Auxiliary readouts only; no cone truth or predicted cone is an input. Reference active mask for regression; test barrier retained.')
(D/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
for f in D.glob('*.py'):ast.parse(f.read_text())
print('Prepared fresh joint model and immutable labels')
