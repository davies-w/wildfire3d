"""Read-only audit of original solver CSVs and independently decoded temperature records."""
from pathlib import Path
import json,tarfile,io,csv,struct,hashlib,time
import numpy as np
R=Path(__file__).parent;X=R.parent.parent/'32_tree_expansion';V=R.parent/'attempt08';cs=json.loads((X/'cases.json').read_text());paths={p.name[:-7]:p for p in (X/'data/cloud_archive').rglob('*.tar.gz')};rows=[];start=time.time();geoms=np.load(X/'data/geometries.npz')
def table(b):
 r=list(csv.reader(io.StringIO(b.decode())));return [s.strip().strip('"') for s in r[1]],np.array(r[2:],float)
def records(b):
 p=0
 while p<len(b):
  n=struct.unpack_from('<i',b,p)[0];assert struct.unpack_from('<i',b,p+4+n)[0]==n;yield memoryview(b)[p+4:p+4+n];p+=n+8
for c in cs:
 n=c['case'];raw=paths[n];cached=R/'data'/(n+'.json')
 if cached.exists():
  row=json.loads(cached.read_text());row['initial_mass_kg']=float(geoms[n].sum()*.125);row['initial_mass_source']='Archived initial weighted particle geometry; device t0 is an uninitialized zero';row['windows']['0-20']['particle_mass_drop_kg']=row['initial_mass_kg']-float(np.interp(20,row['material']['time_s'],row['material']['particle_mass_kg']));cached.write_text(json.dumps(row));rows.append(row);continue
 meta=json.loads(raw.with_name(n+'.summary.json').read_text());assert hashlib.sha256(raw.read_bytes()).hexdigest()==meta['raw_sha256'];h=d=deck=None;temp=None
 with tarfile.open(raw,'r|gz') as tar:
  for m in tar:
   if m.name.endswith('_hrr.csv'):h=table(tar.extractfile(m).read())
   elif m.name.endswith('_devc.csv'):d=table(tar.extractfile(m).read())
   elif m.name.endswith('.fds'):deck=tar.extractfile(m).read();assert hashlib.sha256(deck).hexdigest()==c['deck_sha256']
   elif m.name.endswith('.sf'):
    f=tar.extractfile(m);first=f.read(34)
    if b'TEMPERATURE' not in first:continue
    b=first+f.read();it=records(b);name=bytes(next(it)).decode().strip();next(it);unit=bytes(next(it)).decode().strip();bounds=np.frombuffer(next(it),'<i4');shape=tuple(bounds[1::2]-bounds[::2]+1);tt=[];peaks=[];fullpeaks=[];hots=[];packed=[]
    for rec in it:
     tt.append(float(np.frombuffer(rec,'<f4')[0]));a=np.frombuffer(next(it),'<f4').reshape(shape,order='F');fullpeaks.append(float(a.max()));a=a[1-bounds[0]:49-bounds[0],1-bounds[2]:33-bounds[2],1-bounds[4]:33-bounds[4]];assert a.shape==(48,32,32);peaks.append(float(a.max()));hots.append(int((a>50).sum()));packed.append(np.packbits((a>50).reshape(-1)))
    z=np.load(V/'data/labels'/(n+'.npz'));assert np.array_equal(np.array(packed),z['packed']) and np.array_equal(np.array(tt),z['time']);assert unit=='C';temp=dict(time_s=tt,peak_C=peaks,full_record_peak_C=fullpeaks,hot_cells=hots,viewer_labels_exact=True,bounds=bounds.tolist())
 assert h is not None and d is not None and temp is not None
 hk,ha=h;dk,da=d;ht=ha[:,0];dt=da[:,0];q=ha[:,hk.index('HRR')];ox=ha[:,hk.index('HRR_OX')];mass=da[:,[i for i,k in enumerate(dk) if k.startswith('v0 mass')]].sum(1);fuel=da[:,[i for i,k in enumerate(dk) if k.startswith('v0 fuel')]].sum(1)
 def mean(a,t,lo,hi):
  grid=np.r_[lo,t[(t>lo)&(t<hi)],hi];return float(np.trapezoid(np.interp(grid,t,a),grid)/(hi-lo))
 windows={}
 for lo,hi in [(0,20),(21,40),(40,60),(60,80),(80,100),(100,120),(120,180)]:
  windows[f'{lo}-{hi}']=dict(mean_HRR_kW=mean(q,ht,lo,hi),mean_HRR_OX_kW=mean(ox,ht,lo,hi),released_fuel_vapor_kg=mean(fuel,dt,lo,hi)*(hi-lo),particle_mass_drop_kg=float(np.interp(lo,dt,mass)-np.interp(hi,dt,mass)))
 windows['0-20']['particle_mass_drop_kg']=float(geoms[n].sum()*.125)-float(np.interp(20,dt,mass))
 row=dict(case=n,configuration=c['configuration'],split=c['split'],raw_sha256=meta['raw_sha256'],temperature=temp,hrr=dict(time_s=ht.tolist(),HRR_kW=q.tolist(),HRR_OX_kW=ox.tolist()),material=dict(time_s=dt.tolist(),particle_mass_kg=mass.tolist(),fuel_vapor_kg_s=fuel.tolist()),windows=windows,initial_mass_kg=float(geoms[n].sum()*.125),initial_mass_source='Archived initial weighted particle geometry; device t0 is an uninitialized zero',final_mass_kg=float(mass[-1]),source_deck_lines=[s for s in deck.decode().splitlines() if s.startswith(('&RAMP ID=\'contact\'','&SURF ID=\'contact burner\'','&PART ID=\'contact ignitor\''))]);cached.write_text(json.dumps(row));rows.append(row)
 print('AUDITED',len(rows),n,round(time.time()-start),flush=True)
out=dict(cases=len(rows),viewer_labels_exact_all=all(r['temperature']['viewer_labels_exact'] for r in rows),windows={})
for w in rows[0]['windows']:
 out['windows'][w]={k:dict(min=float(np.min(v)),median=float(np.median(v)),max=float(np.max(v))) for k in rows[0]['windows'][w] for v in [[r['windows'][w][k] for r in rows]]}
out['at_120s_peak_C']=dict(median=float(np.median([np.interp(120,r['temperature']['time_s'],r['temperature']['peak_C']) for r in rows])),max=float(max(np.interp(120,r['temperature']['time_s'],r['temperature']['peak_C']) for r in rows)))
out['late_HRR_above_1kW_cases']=sum(r['windows']['120-180']['mean_HRR_kW']>1 for r in rows)
out['strongest_postsource']=sorted([dict(case=r['case'],mean_HRR_kW=r['windows']['21-40']['mean_HRR_kW'],late_HRR_kW=r['windows']['120-180']['mean_HRR_kW'],mass_fraction_lost=(r['initial_mass_kg']-r['final_mass_kg'])/r['initial_mass_kg']) for r in rows],key=lambda x:x['mean_HRR_kW'],reverse=True)[:10]
(R/'results/summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
