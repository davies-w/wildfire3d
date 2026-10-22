import tarfile
from pathlib import Path
r=Path(__file__).parent
with tarfile.open(r/'data/gpu/cloud/outputs.tar') as t:
 for n in ['data/models/geometry_snapshot.pt','data/models/hybrid.pt']:
  m=t.getmember(n);assert m.isfile();(r/n).write_bytes(t.extractfile(m).read())
