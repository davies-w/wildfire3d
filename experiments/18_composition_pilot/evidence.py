"""Bundle downloaded external cloud evidence, or restore locally without cloud compute."""
import argparse,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('action',choices=['bundle','extract']);a=ap.parse_args();archive=ROOT/'data/cloud-evidence.tar.gz'
if a.action=='bundle':
    with tarfile.open(archive,'w:gz') as t:t.add(ROOT/'data/cloud',arcname='cloud')
else:
    with tarfile.open(archive) as t:t.extractall(ROOT/'data',filter='data')
