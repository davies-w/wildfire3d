"""Extract unchanged four-state definitions from SHA-verified material inputs. No fitting."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
from material_reader import frames
from fortran_records import FortranFile,FortranEOFError
R=Path(__file__).resolve().parent

def table(p):
 with p.open() as f:rows=list(csv.reader(f))
 return rows[1],np.array(rows[2:],float)

def slice_times(p):
 f=FortranFile(p)
 for _ in range(3):f.read_record('u1')
 f.read_ints();tt=[]
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  f.read_reals('f4');tt.append(t)
 return np.array(tt)

def extract(folder,c):
 n=c['case'];proof=json.loads((folder/'verified.json').read_text())
 for name in proof['retained_material_inputs']:
  with (folder/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==proof['members'][name]['sha256'],name
 target=slice_times(next(folder.glob('*.sf')));assert len(target)==91 and target[0]==0 and target[-1]>=179.9 and np.all(np.diff(target)>0)
 pt=[];mass=[];weighted=[]
 for t,ps,labels in frames(folder/(n+'_1.prt5')):
  if not sum(len(x) for x,q in ps[:4]):continue
  mm=[];temps=[]
  for k,(pos,q) in enumerate(ps[:4]):
   assert labels[k][:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR']
   mw=q[:,1]*q[:,2];s=float(mw.sum());mm.append(s);temps.append(float(np.sum(mw*q[:,0])/s) if s else 20.)
  pt.append(t);mass.append(sum(mm));weighted.append(float(np.sum(np.array(mm)*(np.array(temps)-20))))
 pt=np.array(pt);ids=np.abs(pt[:,None]-target).argmin(0);gap=np.abs(pt[ids]-target);assert gap.max()<.21
 wet0=mass[ids[0]];dry0=wet0/(1+c['moisture']);water0=wet0-dry0
 hk,h=table(folder/(n+'_hrr.csv'));dk,a=table(folder/(n+'_devc.csv'));ht=h[:,0];at=a[:,0]
 assert np.all(np.diff(ht)>=0) and np.all(np.diff(at)>=0)
 water=water0-np.cumsum(h[:,hk.index('MLR_WATER VAPOR')]*np.diff(ht,prepend=ht[0]))
 fr=a[:,[j for j,k in enumerate(dk) if k.startswith('v0 fuel')]].sum(1)
 dry=dry0-np.r_[0,np.cumsum((fr[:-1]+fr[1:])*.5*np.diff(at))]/.75
 heat=np.array(weighted)[ids]/wet0
 state=np.stack([np.interp(target,ht,water),np.interp(target,at,dry),np.interp(target,at,fr),heat],-1)
 assert state.shape==(91,4) and np.isfinite(state).all()
 return target,state,{'case':n,'raw_sha256':proof['raw_sha256'],'max_particle_alignment_s':float(gap.max()),'initial_wet_mass_kg':wet0,'state_min':state.min(0).tolist(),'state_max':state.max(0).tolist(),'maximum_water_increase_kg':float(np.diff(state[:,0]).max()),'maximum_dry_increase_kg':float(np.diff(state[:,1]).max())}

def main():
 cases={c['case']:c for c in json.loads((R/'cases.json').read_text())};out=R/'data/four-state';out.mkdir(exist_ok=True);audit=[];pending=[]
 for folder in sorted((R/'data/verified-material').iterdir()):
  if folder.name not in cases or not (folder/'verified.json').exists():continue
  if not list(folder.glob('*.sf')):pending.append(folder.name);continue
  t,state,row=extract(folder,cases[folder.name]);np.savez_compressed(out/(folder.name+'.npz'),time=t.astype('float32'),state=state.astype('float32'));audit.append(row)
 report={'histories':len(audit),'awaiting_exact_timestamps':pending,'training':False,'states':['estimated_remaining_water_kg','estimated_remaining_unreacted_vegetation_kg','vegetation_fuel_release_kg_s','surface_heating_index_K'],'definitions':'Same attempt15/19 formulas: right-endpoint water integral, trapezoidal fuel integral /0.75, initial wet particle mass and dry-basis moisture, mass-weighted particle surface T excess / initial mass. Char inert; gas release is not heat; heating index is not energy. No clamps. Actual slice timestamps retained.','cases':audit}
 (R/'results/four-state-extraction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
if __name__=='__main__':main()
