"""Paired domain sensitivity on verified completed results; no FDS execution."""
from pathlib import Path
import csv,json,math,argparse
import numpy as np
from scipy.io import FortranFile,FortranEOFError
R=Path(__file__).resolve().parent;OLD=R.parent/'48_two_tree_design'
def csv_rows(p):
 with p.open() as f:
  q=csv.reader(f);next(q);keys=[x.strip().strip('"') for x in next(q)];a=np.array(list(q),float)
 assert np.isfinite(a).all();assert np.all(np.diff(a[:,0])>=0);return {k:a[:,i] for i,k in enumerate(keys)}
def integral(t,y,start=0):
 assert t[-1]>=180-1e-5
 tt=np.unique(np.r_[start,t[(t>start)&(t<180)],180.]);return float(np.trapezoid(np.interp(tt,t,y),tt))
def scalar_compare(old,new,olddev,newdev,initial):
 ot,nt=old['Time'],new['Time'];oy,ny=old['HRR'],new['HRR'];t=np.unique(np.r_[ot,nt]);t=t[(t>=0)&(t<=180)];oe=integral(ot,oy);ne=integral(nt,ny);op=integral(ot,oy,20);nn=integral(nt,ny,20)
 loss=lambda d:1-sum(v[-1] for k,v in d.items() if k.endswith(' mass'))/initial
 rel=lambda a,b:(b-a)/max(abs(a),1e-9)
 m=dict(original_energy_kj=oe,compact_energy_kj=ne,total_energy_relative_difference=rel(oe,ne),original_post20_energy_kj=op,compact_post20_energy_kj=nn,post20_energy_relative_difference=rel(op,nn),peak_hrr_relative_difference=rel(float(max(oy)),float(max(ny))),hrr_history_relative_L1=float(np.trapezoid(np.abs(np.interp(t,ot,oy)-np.interp(t,nt,ny)),t))/max(oe,1e-9),wet_mass_loss_difference_percentage_points=100*(loss(newdev)-loss(olddev)))
 limits={'total_energy_relative_difference':.10,'post20_energy_relative_difference':.10,'peak_hrr_relative_difference':.20,'hrr_history_relative_L1':.20,'wet_mass_loss_difference_percentage_points':2.}
 m['major_metric_flags']=[k for k,v in limits.items() if abs(m[k])>v];return m
def frames(path,indices):
 f=FortranFile(path);name=f.read_record('u1').tobytes().decode().strip();f.read_record('u1');unit=f.read_record('u1').tobytes().decode().strip();b=f.read_ints();assert name=='TEMPERATURE' and unit=='C';shape=tuple(b[1::2]-b[::2]+1);ix=[v-b[2*i] for i,v in enumerate(indices)];assert all(v.min()>=0 and v.max()<shape[i] for i,v in enumerate(ix))
 previous=-1
 try:
  while True:
   try:t=float(f.read_reals('f4')[0])
   except FortranEOFError:break
   a=f.read_reals('f4').reshape(shape,order='F');assert t>=previous;previous=t;yield t,a[np.ix_(*ix)].copy()
 finally:f.close()
def field_compare(op,npth,c):
 nx,ny,nz=[round(d/.5) for d in c['domain']];offset=round((c['original_domain'][1]/2-8)/.5)
 oi=[np.arange(1,nx+1),np.arange(1,ny+1)+offset,np.arange(1,nz+1)];ni=[np.arange(1,n+1) for n in [nx,ny,nz]]
 old=iter(frames(op,oi));lo=next(old);hi=next(old);hoterr=0.;hotcount=0;peaks=[];count=0
 for t,a in frames(npth,ni):
  while hi[0]<t-1e-5:
   lo=hi
   try:hi=next(old)
   except StopIteration:assert abs(lo[0]-t)<.1;hi=lo;break
  assert lo[0]<=t+.1 and hi[0]>=t-.1
  alpha=0 if hi[0]==lo[0] else min(1,max(0,(t-lo[0])/(hi[0]-lo[0])));b=lo[1]*(1-alpha)+hi[1]*alpha
  mask=(a>=50)|(b>=50);hoterr+=float(np.abs(a-b)[mask].sum(dtype='f8'));hotcount+=int(mask.sum());peaks.append(abs(float(a.max())-float(b.max())));count+=1
 assert count>=80
 return dict(common_region_hot_temperature_mae_C=hoterr/max(1,hotcount),peak_temperature_history_mae_C=float(np.mean(peaks)),frames=count,alignment='Same0.5m cell centers after transverse translation; old frames linearly interpolated to new times. Hot union >=50C; average over sampled hot cells and times, not volume-wide cold background.')
def main():
 cases=json.loads((R/'data/cases.json').read_text());proof=json.loads((R/'data/completed/proof.json').read_text());assert proof['passed'] and len(proof['cases'])==22
 originals={}
 for group in ['canaries04','completed05','completed06','completed07']:
  for p in (OLD/'data'/group).glob('*/solve'):originals[p.parent.name]=p
 rows=[]
 for c in cases:
  o=originals[c['original_case']];n=R/'data/completed'/c['pilot_case']/'solve';on=c['original_case'];nn=c['pilot_case'];config=next(v for v in json.loads((OLD/'data/pilot/cases.json').read_text()) if v['pilot_case']==on);c['original_domain']=config['domain']
  m=scalar_compare(csv_rows(o/(on+'_hrr.csv')),csv_rows(n/(nn+'_hrr.csv')),csv_rows(o/(on+'_devc.csv')),csv_rows(n/(nn+'_devc.csv')),sum(c['expected_wet_mass_kg'].values()))
  f=field_compare(o/(on+'_1_1.sf'),n/(nn+'_1_1.sf'),c)
  flags=m['major_metric_flags']+[k for k in ['common_region_hot_temperature_mae_C','peak_temperature_history_mae_C'] if f[k]>100]
  rows.append(dict(case=nn,original_case=on,metrics=m,temperature=f,major_discrepancy_flags=flags));print(nn,flags,flush=True)
 controls=[]
 for c in cases:
  if c['comparison_variant']!='height_control':continue
  name=c['pilot_case'];base=name.replace('_expanded','_baseline');bc=next(x for x in cases if x['pilot_case']==base)
  a=R/'data/completed'/base/'solve';b=R/'data/completed'/name/'solve'
  m=scalar_compare(csv_rows(a/(base+'_hrr.csv')),csv_rows(b/(name+'_hrr.csv')),csv_rows(a/(base+'_devc.csv')),csv_rows(b/(name+'_devc.csv')),sum(c['expected_wet_mass_kg'].values()))
  region={'domain':bc['domain'],'original_domain':bc['domain']}
  f=field_compare(a/(base+'_1_1.sf'),b/(name+'_1_1.sf'),region)
  flags=m['major_metric_flags']+[k for k in ['common_region_hot_temperature_mae_C','peak_temperature_history_mae_C'] if f[k]>100]
  controls.append(dict(baseline=base,height_control=name,common_region_m=bc['domain'],metrics=m,temperature=f,major_discrepancy_flags=flags))
 assert len(controls)==2
 out=R/'data/comparison';out.mkdir(exist_ok=True);(out/'summary.json').write_text(json.dumps(dict(complete=True,cases=rows,vertical_controls=controls,vertical_controls_pass_screening=all(not x['major_discrepancy_flags'] for x in controls),all_pass_screening=all(not x['major_discrepancy_flags'] for x in rows),limitations='Engineering screening only, not statistical equivalence or physical/grid validation; global integration volume changes; no uncertainty ensemble.'),indent=2)+'\n')
if __name__=='__main__':main()
