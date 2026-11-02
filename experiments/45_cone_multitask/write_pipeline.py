"""Declare exact source dependencies and public scientific output stages."""
from pathlib import Path
import json,yaml
R=Path(__file__).resolve().parent;records=json.loads((R/'data/labels/schema.json').read_text())['source_records']
source_deps=['../../'+r['source_path'] for r in records if r['split']!='train']
stages=dict(
 labels=dict(cmd='../../.venv/bin/python prepare_labels.py',deps=['prepare_labels.py','../44_hot_gas_cones/cones.py','../44_hot_gas_cones/extract_training.py','../44_hot_gas_cones/data/training-plan.json','../44_hot_gas_cones/data/training-histories','../36_tree_density/learning-schema.json','../36_tree_density/data/learning/sequences.npz','../36_tree_density/cases.json','../35_surrogate_diagnostics/attempt12/inventory.json',*source_deps],outs=['data/labels','data/heldout-cones']),
 prepare=dict(cmd='../../.venv/bin/python prepare.py && ../../.venv/bin/python validate.py && ../../.venv/bin/python build_pool.py',deps=['prepare.py','validate.py','build_pool.py','model.py','gated_model.py','worker.py','joint_objective.py','cloud_check.py','data/labels','../41_dropout10_from_start/data/training/objective.py','../41_dropout10_from_start/data/training/runtime.py','../41_dropout10_from_start/data/training/schema.json','../41_dropout10_from_start/data/training/data/sequences.npz','../41_dropout10_from_start/data/training/coverage-plan.json','../38_history8_shared64/data/training08/bootstrap.py','../38_history8_shared64/data/training08/workflow.yaml'],outs=['data/training']),
 prepare_pool02=dict(cmd='../../.venv/bin/python prepare02.py && ../../.venv/bin/python build_pool02.py',deps=['prepare02.py','build_pool02.py','data/training'],outs=['data/training02']),
 progress=dict(cmd='../../.venv/bin/python snapshot_progress.py',deps=['snapshot_progress.py','plot_learning_curve.py'],outs=['data/progress-public']),
 collect=dict(cmd='../../.venv/bin/python collect.py',deps=['collect.py'],outs=['data/pool02-results']))
(R/'dvc.yaml').write_text(yaml.safe_dump(dict(stages=stages),sort_keys=False))
