"""Extract the DVC-tracked cloud evidence input without launching cloud resources."""
import tarfile
from study import ROOT
with tarfile.open(ROOT/'data/cloud-evidence.tar.gz') as archive:
    archive.extractall(ROOT/'data',filter='data')
