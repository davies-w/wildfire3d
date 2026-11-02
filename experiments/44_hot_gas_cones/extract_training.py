"""Read one SHA-verified source at a time; fit fixed cones on TRAIN only."""
from pathlib import Path
import argparse,hashlib,io,json,struct,tarfile,time,fcntl
import numpy as np
from cones import fit,membership,metrics,ellipsoid,COVERAGE,THRESHOLD_C
R=Path(__file__).resolve().parent;repo=R.parents[1]
xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in (48,32,32)],indexing='ij'),-1).reshape(-1,3)
ind=np.indices((48,32,32));boundary=np.any((ind==0)|(ind==np.array([47,31,31])[:,None,None,None]),axis=0)
def record(f):
    head=f.read(4)
    if not head:return None
    assert len(head)==4;n=struct.unpack('<I',head)[0];b=f.read(n);tail=f.read(4)
    assert len(b)==n and len(tail)==4 and struct.unpack('<I',tail)[0]==n
    return b

def read_temperature(f,origin):
    assert record(f).decode().strip()=='TEMPERATURE';record(f);assert record(f).decode().strip()=='C'
    bounds=np.frombuffer(record(f),dtype='<i4');shape=tuple(bounds[1::2]-bounds[::2]+1)
    ii=[np.rint((np.arange(n)*.5+.25-origin[k])/.5+.5).astype(int)-bounds[2*k] for k,n in enumerate([48,32,32])]
    assert all(v.min()>=0 and v.max()<shape[k] for k,v in enumerate(ii))
    while True:
        b=record(f)
        if b is None:break
        t=float(np.frombuffer(b,dtype='<f4')[0]);a=np.frombuffer(record(f),dtype='<f4').reshape(shape,order='F');a=a[np.ix_(*ii)]
        assert a.shape==(48,32,32) and np.isfinite(a).all()
        yield t,a.reshape(-1).astype(float)

def source_frames(item):
    p=repo/item['path']
    with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==item['sha256'],item['case']
    if item['source_kind']=='verified_temperature_slice':
        with p.open('rb') as f:yield from read_temperature(f,item['origin_m'])
    else:
        found=False
        # Stream the existing gzip archive; no extraction directory or decoded array copy.
        with tarfile.open(p,mode='r|gz') as tar:
            for m in tar:
                if not m.isfile() or not m.name.endswith('.sf'):continue
                f=tar.extractfile(m);first=record(f)
                if first.decode().strip()!='TEMPERATURE':continue
                assert not found;found=True
                # Only this temperature member is buffered (about20MB); discarded after history.
                prefix=struct.pack('<I',len(first))+first+struct.pack('<I',len(first))
                with io.BytesIO(prefix+f.read()) as stream:yield from read_temperature(stream,item['origin_m'])
                break
        assert found,'Missing temperature volume: '+item['case']

def frame(temp,h,t):
    hot=temp>THRESHOLD_C;c=fit(xyz[hot],h)
    row=dict(time_s=t,active=bool(hot.any()),domain_peak_temperature_C=float(temp.max()),igniter_on=bool(t<20))
    if c is None:row.update(cone=None,cone_metrics=None,ovoid_metrics=None,ovoid95_metrics=None);return row
    volume,pivot,tilt,length,radius=c;mask=membership(xyz,pivot,tilt,length,radius);oval,center,cov=ellipsoid(xyz,hot,temp)
    ev,v=np.linalg.eigh(cov);d=xyz-center;dist=np.sum((d@v)**2/np.maximum(ev,1e-12),axis=1);k=int(np.ceil(COVERAGE*hot.sum()));cut=float(np.partition(dist[hot],k-1)[k-1]);oval95=dist<=cut+1e-9
    row.update(cone=dict(pivot_height_m=pivot,tilt_from_vertical_deg=tilt,length_m=length,end_radius_m=radius,peak_temperature_C=float(temp[mask].max())),cone_metrics=metrics(mask,hot),ovoid_metrics=metrics(oval,hot),ovoid95_metrics=metrics(oval95,hot),temperature_excess_capture=float(np.sum(temp[mask&hot]-20)/np.sum(temp[hot]-20)),analytic_cone_volume_m3=float(volume),in_domain_cone_volume_m3=float(mask.sum()*.125),apex_below_crown=bool(pivot<2),peak_temperature_missed_C=float(temp.max()-temp[mask].max()),hot_cells_on_domain_boundary=int(hot.reshape(48,32,32)[boundary].sum()))
    assert row['cone_metrics']['hot_recall']>=COVERAGE-1e-9
    return row

def code_hash():
    return hashlib.sha256((R/'cones.py').read_bytes()+(R/'extract_training.py').read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int);args=ap.parse_args();plan=json.loads((R/'data/training-plan.json').read_text());out=R/'data/training-histories';out.mkdir(exist_ok=True)
    with (R/'data/training-extraction.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with np.load(repo/'experiments/36_tree_density/data/learning/sequences.npz') as seq:expected=seq['time'][[x['case_index'] for x in plan['cases']]]
        recipe=code_hash();start=time.monotonic();new=0
        for j,item in enumerate(plan['cases']):
            dest=out/(item['case']+'.json')
            if dest.exists():
                prior=json.loads(dest.read_text());assert prior['recipe_sha256']==recipe and prior['source_sha256']==item['sha256'];continue
            rows=[frame(temp,item['crown_height_m'],t) for t,temp in source_frames(item)]
            times=np.array([r['time_s'] for r in rows]);assert len(rows)==91 and np.allclose(times,expected[j],rtol=0,atol=1e-5),item['case']
            result=dict(case=item['case'],case_index=item['case_index'],rotation=0,split='train',fold=item['fold'],physical_key=item['physical_key'],source_sha256=item['sha256'],raw_sha256=item['raw_sha256'],recipe_sha256=recipe,snapshots=rows)
            partial=dest.with_suffix('.partial');partial.write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n');partial.replace(dest);new+=1
            if new%10==0 or j==len(plan['cases'])-1:print(json.dumps(dict(completed=j+1,total=len(plan['cases']),case=item['case'],elapsed_s=round(time.monotonic()-start))),flush=True)
            if args.limit and new>=args.limit:break
if __name__=='__main__':main()
