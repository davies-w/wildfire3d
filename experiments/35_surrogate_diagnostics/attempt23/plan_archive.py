"""Save an archive sync plan without applying it or uploading any object.

Replanning observes the local mirror and remote listing at that time. It
cannot recreate the original remote state or original timestamp byte for byte.
The historical plan is preserved, not a current publication recommendation.
"""
from pathlib import Path
from huggingface_hub import HfApi


def main():
    root = Path(__file__).resolve().parent
    source = root.parents[2] / 'FDS/hf_dvc_mirror'
    plan = HfApi().sync_bucket(
        str(source), 'hf://buckets/wdavies/dvc_storage/wildfire3d',
        ignore_existing=True, delete=False,
        plan=str(root / 'data/archive-sync-plan.jsonl'), quiet=True,
    )
    assert not any(operation.action == 'delete' for operation in plan.operations)


if __name__ == '__main__':
    main()
