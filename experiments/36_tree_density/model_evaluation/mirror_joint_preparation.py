"""Push only the adopted joint package to the authorized local DVC mirror."""
from pathlib import Path
from dvc.repo import Repo
R=Path(__file__).resolve().parents[1]
with Repo(str(R.parents[1])) as repo:
    stage=repo.stage.get_target(str(R/'dvc.yaml')+':prepare_joint_trial')
    for objects in stage.get_used_objs().values():
        result=repo.cloud.push(objects,remote='mirror',jobs=4);assert not result.failed
print('Joint package preserved in local mirror; no public remote used')
