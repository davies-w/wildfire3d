"""Restore pinned external evidence archives; never launch paid work."""
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for name in ('reuse18','reuse19'):
    dest=ROOT/'data'/name;dest.mkdir(exist_ok=True)
    with tarfile.open(ROOT/'data'/(name+'.tar.gz')) as t:t.extractall(dest,filter='data')
