"""Independent raw HRR-device cross-check for full-resolution slice extraction."""
import csv,json
import numpy as np
from fields import ROOT,read_slice

def verify(c):
 folder=ROOT/'data/cloud'/c['case'];path=next(p for p in folder.glob('*.sf') if read_header(p)=='HRRPUV')
 _,units,bounds,t,a=read_slice(path)
 # Standard-domain full cell volume, excluding low boundary planes; expanded slices are ROI only.
 if c.get('expanded'):return {'case':c['case'],'skipped':'expanded ROI excludes external heat release'}
 q=a[:,1:,1:,1:].sum((1,2,3))*.125
 with next(folder.glob('*_hrr.csv')).open() as f:rows=list(csv.reader(f))
 keys=[v.strip().strip('"') for v in rows[1]];d=np.array(rows[2:],float);reference=np.interp(t,d[:,0],d[:,keys.index('HRR')]);active=reference>100
 relative=float(np.median(abs(q[active]-reference[active])/reference[active])) if active.any() else None
 r=dict(case=c['case'],units=units,active_median_relative_difference=relative,peak_integrated_kW=float(q.max()),peak_device_kW=float(reference.max()),note='Instantaneous slice compared with interpolated device samples; time averaging can differ.')
 assert units=='kW/m3',r
 r['screen_over_10pct']=relative is not None and relative>=.1
 r['not_an_equality_test']='FDS DUMP_HRR divides timestep-integrated Q_DOT_SUM by output interval; slice is instantaneous. Raw decoder equality is independently checked by verify_ascii.py.'
 return r
def read_header(p):
 from scipy.io import FortranFile
 return FortranFile(p).read_record('u1').tobytes().decode().strip()
if __name__=='__main__':
 rows=[verify(c) for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='pilot'];(ROOT/'results/field-verification.json').write_text(json.dumps(rows,indent=2));print(rows)
