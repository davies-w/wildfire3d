from pathlib import Path
import tarfile,json,hashlib,io
R=Path(__file__).parent
files=[R/n for n in ['sequence.py','worker.py','original_cnn.py','previous_loss.py','snapshot_evaluation.py','cases.json']]+[R/'data/geometry.npy',*sorted((R/'data').glob('*-material.npz'))]
h={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with tarfile.open(R/'data/overlay.tar','w') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)))
 raw=json.dumps(h,indent=2).encode();ti=tarfile.TarInfo('overlay-hashes.json');ti.size=len(raw);tar.addfile(ti,io.BytesIO(raw))
(R/'results/input-freeze.json').write_text(json.dumps(h,indent=2));print('Overlay bytes',(R/'data/overlay.tar').stat().st_size)
