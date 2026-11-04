"""Independently check saved temperature values with fds2ascii; never runs FDS."""
from compare import *
import subprocess,tempfile,hashlib
root=R.parents[1];binary=root/'FDS/install/bin/fds2ascii';rows=[]
for group in [R/'data/completed',OLD/'data/canaries04',OLD/'data/completed05',OLD/'data/completed06',OLD/'data/completed07']:
 for folder in sorted(group.glob('*/solve')):
  case=folder.parent.name;path=folder/(case+'_1_1.sf')
  samples=list(frames(path,[np.array([1])]*3));times=[t for t,a in samples]
  assert times[0]==0 and abs(times[-1]-180)<.01 and len(times)>=6
  with tempfile.TemporaryDirectory() as td:
   for p in folder.iterdir():
    if p.is_file():(Path(td)/p.name).symlink_to(p)
   output=Path(td)/'sample.csv';inp=f'{case}\n2\n8\nn\n179.99 180.01\n1\n1\n{output}\n'
   q=subprocess.run([str(binary)],cwd=td,input=inp,text=True,capture_output=True,timeout=60);assert q.returncode==0 and output.exists(),q.stderr
   table=np.loadtxt(output,delimiter=',',skiprows=2);idx=[np.unique(np.rint(table[:,i]/.5).astype(int)) for i in range(3)]
   last=list(frames(path,idx))[-1][1];expected=last.ravel(order='F');assert len(expected)==len(table)
   assert np.allclose(expected,table[:,3],rtol=6e-5,atol=.006)
   rows.append(dict(case=case,frames=len(times),times_s=times,ascii_samples=len(table),max_ascii_rounding_error_C=float(np.max(np.abs(expected-table[:,3])))))
assert len(rows)==44
out=R/'data/field-verification';out.mkdir(exist_ok=True)
(out/'proof.json').write_text(json.dumps(dict(passed=True,cases=rows,converter_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),coordinate_note='fds2ascii prints grid-node coordinates for cell-centered values. Its printed coordinate divided by 0.5 identifies the stored index, not the physical center. FDS dump.f90 cell-centered branch writes QUANTITY(I,J,K) directly; interior indices1..N correspond to centers(i-0.5)*0.5. Comparison uses these interior indices and integer transverse translation.',limitation='3D snapshots are sparse: default DT_SL3D=180/5=36s; DT_SLCF=2 controls 2D slices. This cannot rule out transient temperature differences between saved frames.'),indent=2)+'\n')
print('Verified44 actual slice files against fds2ascii')
