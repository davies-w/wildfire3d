"""Archive existing cloud data; never submit compute or delete source objects."""
from pathlib import Path
import subprocess,json,time
R=Path(__file__).parent;G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';dest=R/'data/cloud_archive';dest.mkdir(exist_ok=True)
subprocess.run([G,'storage','rsync','--recursive','gs://tmrw-wildfire-20261015-trial/expansion32/',str(dest)],check=True)
(R/'results/cloud-archive-collected.json').write_text(json.dumps(dict(complete=True,collected_unix=time.time(),source='gs://tmrw-wildfire-20261015-trial/expansion32/',files=sum(1 for p in dest.rglob('*') if p.is_file()),bytes=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())),indent=2))
