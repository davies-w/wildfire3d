"""Decode cell-centered FDS fields; retain 0.5 m cells, no spatial pooling."""
import json,csv
from pathlib import Path
import numpy as np
from fortran_records import FortranFile,FortranEOFError
ROOT=Path(__file__).parent
trapezoid=getattr(np,'trapezoid',None) or getattr(np,'trapz')
NAMES=['TEMPERATURE','HRRPUV','U-VELOCITY','V-VELOCITY','W-VELOCITY','INTEGRATED INTENSITY']
def read_slice(path):
 f=FortranFile(path);name=f.read_record('u1').tobytes().decode().strip();short=f.read_record('u1');unit=f.read_record('u1').tobytes().decode().strip();bounds=f.read_ints();shape=tuple(bounds[1::2]-bounds[::2]+1);times=[];values=[]
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  values.append(f.read_reals('f4').reshape(shape,order='F'));times.append(t)
 return name,unit,bounds,np.array(times),np.stack(values)
def extract(c):
 if c['split']=='test':assert (ROOT/'results/prediction-freeze.json').exists()
 folder=ROOT/'data/cloud'/c['case'];out=ROOT/'data/fields';out.mkdir(exist_ok=True)
 sources={}
 for path in folder.glob('*.sf'):
  name,unit,bounds,t,a=read_slice(path)
  if name not in NAMES:continue
  # FDS SLCC output is indexed by mesh cells including low-side boundary plane.
  # Select physical centers .25:.5:23.75 etc; same ROI in expanded domain.
  origin=np.array([-4,-4,0]) if c.get('expanded') else np.zeros(3)
  ii=[np.rint((np.arange(n)*.5+.25-origin[k])/.5+.5).astype(int)-bounds[2*k] for k,n in enumerate([48,32,32])]
  a=a[:,ii[0]][:,:,ii[1]][:,:,:,ii[2]]
  assert a.shape[1:]==(48,32,32) and np.isfinite(a).all()
  sources[name]=(unit,t,a)
 assert set(sources)==set(NAMES),list(sources)
 times=sources[NAMES[0]][1]
 assert times[-1]>=179.9
 for name in NAMES:assert np.allclose(times,sources[name][1])
 values=np.stack([sources[name][2] for name in NAMES],axis=1).astype('float32')
 np.save(out/(c['case']+'.npy'),values);np.save(out/(c['case']+'-time.npy'),times)
 with (folder/(c['case']+'_devc.csv')).open() as f:rows=list(csv.reader(f))
 keys=[v.strip().strip('"') for v in rows[1]];dv=np.array(rows[2:],float);post=dv[:,0]>=21;rate=sum(dv[:,j] for j,k in enumerate(keys) if k.startswith('v0 fuel'))
 report=dict(case=c['case'],shape=list(values.shape),units={n:sources[n][0] for n in NAMES},post_source_fuel_kg=float(trapezoid(rate[post],dv[post,0])),post_source_peak_HRRPUV=float(values[times>=21,1].max()),post_source_peak_temperature_C=float(values[times>=21,0].max()),field_extent=[0,24,0,16,0,16],dx=.5,radiation='Integrated intensity; not directional surface irradiance',time_end=float(times[-1]))
 (out/(c['case']+'.json')).write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');a=p.parse_args();c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['case']==a.case);print(json.dumps(extract(c),indent=2))
