import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
dest=ROOT/'data/reused';dest.mkdir(exist_ok=True)
with tarfile.open(ROOT/'data/reused-evidence.tar.gz') as t:t.extractall(dest,filter='data')
