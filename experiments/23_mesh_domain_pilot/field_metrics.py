"""Read raw FDS cell-centred3D slices; compare common1m gas volumes."""
import json
from pathlib import Path
import numpy as np
from scipy.io import FortranFile,FortranEOFError
ROOT=Path(__file__).parent

def load(c):
 folder=ROOT/'data/cloud'/c['case'];data={};dx=c['dx']
 for p in folder.glob('*.sf'):
  f=FortranFile(p);quantity=f.read_record('u1').tobytes().decode().strip();f.read_record('u1');f.read_record('u1');bounds=f.read_ints();shape=tuple(bounds[2*i+1]-bounds[2*i]+1 for i in range(3));times=[];frames=[];native=[]
  if quantity not in ['TEMPERATURE','HRRPUV']:continue
  while True:
   try:t=float(f.read_reals('f4')[0])
   except FortranEOFError:break
   a=f.read_reals('f4').reshape(shape,order='F')
   origin=(-6,-6,0) if c['expanded'] else (0,0,0)
   indices=[np.flatnonzero((origin[i]+(np.arange(bounds[2*i],bounds[2*i+1]+1)-.5)*dx>0)&(origin[i]+(np.arange(bounds[2*i],bounds[2*i+1]+1)-.5)*dx<[20,20,15][i])) for i in range(3)]
   a=a[np.ix_(*indices)]
   assert a.shape==tuple(int(v/dx) for v in [20,20,15]);native.append(float(a.max()))
   if dx==.5:a=a.reshape(20,2,20,2,15,2).mean(axis=(1,3,5))
   frames.append(a);times.append(t)
  data[quantity]=(np.array(times),np.array(frames),native)
 return data

def main():
 cases=[c for c in json.loads((ROOT/'cases.json').read_text()) if (ROOT/'data/cloud'/c['case']/'result.json').exists()];datasets={c['case']:load(c) for c in cases};rows=[]
 xyz=np.meshgrid(np.arange(20)+.5,np.arange(20)+.5,np.arange(15)+.5,indexing='ij');x,y,z=xyz;gas=~((x>=11)&(x<=17)&(y>=8)&(y<=14)&(z<=5))
 for i,a in enumerate(cases):
  for b in cases[i+1:]:
   if a['layout']!=b['layout'] or (a['dx']!=b['dx'] and a['expanded']!=b['expanded']):continue
   r=dict(a=a['case'],b=b['case'],quantities={})
   for q in ['TEMPERATURE','HRRPUV']:
    ta,aa,pa=datasets[a['case']][q];tb,bb,pb=datasets[b['case']][q];pairs=[(i,int(np.argmin(abs(tb-t)))) for i,t in enumerate(ta) if t<=min(ta[-1],tb[-1])+.01];pairs=[(i,j) for i,j in pairs if abs(ta[i]-tb[j])<.05]
    ia,ib=np.array(pairs).T;av=aa[ia][:,gas];bv=bb[ib][:,gas];threshold=100 if q=='TEMPERATURE' else 10;active=(av>threshold)|(bv>threshold);diff=abs(av-bv)
    r['quantities'][q]=dict(common_end_s=float(ta[ia[-1]]),frames=len(pairs),whole_gas_MAE=float(diff.mean()),active_union_MAE=float(diff[active].mean()) if active.any() else None,active_threshold=threshold,final_map_MAE=float(diff[-1].mean()),final_active_volume_a_m3=int((av[-1]>threshold).sum()),final_active_volume_b_m3=int((bv[-1]>threshold).sum()),native_peak_a=max(pa),native_peak_b=max(pb))
   rows.append(r)
 (ROOT/'results/field-comparison.json').write_text(json.dumps(dict(pairs=rows,method='Raw .sf Fortran records; Select cell centres by mesh origin+(index-0.5)*dx within common physical0:20,0:20,0:15m region, excluding both low ghost slab and expanded-domain high padding. Fine2x2x2 cells volume-averaged onto common1m cells; building-solid cells excluded. Temperature active>100C,HRRPUV active>10kW/m3 are descriptive masks, not pass/fail gates. No image-derived values; instantaneous turbulent differences do not alone establish bias.'),indent=2));print('Raw3D comparisons',len(rows))
if __name__=='__main__':main()
