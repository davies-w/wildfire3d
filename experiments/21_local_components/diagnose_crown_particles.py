"""Read raw particle archives and separate spatially disjoint static crowns."""
from scipy.io import FortranFile,FortranEOFError
import numpy as np,json
from scene import ROOT
results=[]
for name in ['ac21_double','ac21_double_expanded','ac21_double_fine']:
 f=FortranFile(ROOT/'data/cloud'/name/(name+'_1.prt5'))
 assert int(f.read_ints()[0])==1
 version=int(f.read_ints()[0]);nc=int(f.read_ints()[0]);labels=[]
 for c in range(nc):
  nq=int(f.read_ints()[0]);quant=[]
  for j in range(nq):
   quant.append(bytes(f.read_record('u1')).decode().strip());f.read_record('u1')
  labels.append(quant)
 peaks={size:{c:dict(max_C=-1,time_s=None,max_C_after22=-1) for c in range(4)} for size in ['small','large']}
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  for c in range(nc):
   n=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,n);tags=f.read_ints();q=f.read_reals('f4').reshape(len(labels[c]),n) if labels[c] else None
   if c>=4 or n==0:continue
   temp=q[labels[c].index('PARTICLE TEMPERATURE')]
   for size,mask in [('small',xyz[1]<15),('large',xyz[1]>=15)]:
    if not mask.any():continue
    v=float(max(temp[mask]));r=peaks[size][c]
    if v>r['max_C']:r.update(max_C=v,time_s=t)
    if t>=22:r['max_C_after22']=max(r['max_C_after22'],v)
 results.append(dict(case=name,classes=['foliage','small roundwood','medium roundwood','large roundwood'],particle_temperature=peaks,method='Raw prt5 all-sampled static particles split by y<15 vs y>=15; archive layout verified against FDS dump.f90. Temperature alone is not a combustion-rate measurement.'))
(ROOT/'results/crown-particle-diagnosis.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
