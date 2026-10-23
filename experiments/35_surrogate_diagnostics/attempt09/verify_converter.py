"""Cross-check an original 3D temperature file using the installed official fds2ascii."""
from pathlib import Path
import sys,subprocess,json,tarfile,numpy as np
R=Path(__file__).resolve().parent;repo=R.parents[2];sys.path.insert(0,str(repo));from paths import DIST
sys.path.insert(0,str(repo/'experiments/32_tree_expansion'));from fields import read_slice
out=R/'data/independent';out.mkdir(exist_ok=True);name='x32_066_s0';raw=next((repo/'experiments/32_tree_expansion/data/cloud_archive').rglob(name+'.tar.gz'))
with tarfile.open(raw,'r|gz') as tar:
 for m in tar:
  if m.name.endswith('.smv'):(out/Path(m.name).name).write_bytes(tar.extractfile(m).read())
  elif m.name.endswith('.sf'):
   f=tar.extractfile(m);h=f.read(34)
   if b'TEMPERATURE' in h:(out/Path(m.name).name).write_bytes(h+f.read())
stdin=name+'\n2\n1\nn\n120 124\n1\n1\nlate-temperature.csv\n';result=subprocess.run([str(Path(DIST)/'bin/fds2ascii')],cwd=out,input=stdin,text=True,capture_output=True,check=True,timeout=60);(out/'converter-stdout.txt').write_text(result.stdout)
_,_,bounds,t,a=read_slice(out/(name+'_1_1.sf'));csv=np.loadtxt(out/'late-temperature.csv',delimiter=',',skiprows=2);mean=a[(t>=120)&(t<=124)].mean(0);err=float(abs(mean.ravel(order='F')-csv[:,3]).max());assert err<.001
(R/'results/independent-converter.json').write_text(json.dumps(dict(case=name,interval_s=[120,124],records_averaged=t[(t>=120)&(t<=124)].tolist(),max_absolute_error_C=err,converter_peak_C=float(csv[:,3].max()),physical_cell_peak_average_C=float(mean[1:,1:,1:].max()),full_record_max_index=list(map(int,np.unravel_index(mean.argmax(),mean.shape))),passed=True,scope='Official converter agrees with raw-array decode including boundary index-zero records; physical cell centers use indices1..48,1..32,1..32.'),indent=2))
