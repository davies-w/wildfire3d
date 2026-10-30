"""Retain initial failure diagnostics from the verified preemption archive."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;out=R/'data/failure01';out.mkdir(exist_ok=True)
for name in ['timing-check.json','optimizer-resume-check.json','job-status.json']:
 src=R/'data/preempted01'/name
 assert src.is_file(),src
 shutil.copy2(src,out/name)
