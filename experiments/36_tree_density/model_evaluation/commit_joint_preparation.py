"""Adopt only this experiment's existing outputs using DVC's stage API.

The repository-wide graph currently has overlapping outputs in experiment21.
Targeted stage save/commit avoids changing that unrelated experiment and still
uses DVC hashing, cache adoption and lock serialization (no solver/training).
"""
from pathlib import Path
from dvc.repo import Repo
R=Path(__file__).resolve().parents[1]
with Repo(str(R.parents[1])) as repo:
    with repo.lock:
        stages=[repo.stage.get_target(str(R/'dvc.yaml')+':'+n) for n in ['validate_joint_pipeline','prepare_joint_trial','validate_joint_trial']]
        for stage in stages:
            stage.save();stage.commit()
        stages[0].dvcfile.dump_stages(stages,update_pipeline=False)
print('Adopted existing joint outputs in DVC cache and lock; no stage executed')
