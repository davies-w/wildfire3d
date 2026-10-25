"""Non-deleting public archive sync in sequential batches after earlier429 evidence."""
from pathlib import Path
from huggingface_hub import HfApi
import time
R=Path(__file__).resolve().parent;repo=R.parents[2];api=HfApi();source=repo/'FDS/hf_dvc_mirror'
plan=api.sync_bucket(str(source),'hf://buckets/wdavies/dvc_storage/wildfire3d',ignore_existing=True,delete=False,plan=str(R/'data/archive-sync-plan.jsonl'),quiet=True)
assert not any(x.action=='delete' for x in plan.operations)
ops=[x for x in plan.operations if x.action=='upload']
for j in range(0,len(ops),25):
 api.batch_bucket_files('wdavies/dvc_storage',add=[(str(source/x.path),'wildfire3d/'+x.path) for x in ops[j:j+25]])
 print('Archived',min(j+25,len(ops)),'of',len(ops),flush=True);time.sleep(2)
