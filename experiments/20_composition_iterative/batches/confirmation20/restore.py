import tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
with tarfile.open(p/'data/cloud-evidence.tar.gz') as t:t.extractall(p/'data',filter='data')
