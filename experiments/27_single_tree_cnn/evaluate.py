"""Evaluate frozen full-field predictions; physical units and hot-region errors."""
import json,hashlib
import numpy as np
from scipy.ndimage import uniform_filter1d
from cnn import ROOT,load

def metrics(a,b,ambient_radiation=None):
 ambient=a[0,5] if ambient_radiation is None else ambient_radiation
 ra=np.maximum(a[:,5]-ambient,0).sum(0);rb=np.maximum(b[:,5]-ambient,0).sum(0)
 d=np.abs(a-b);active=(a[:,0]>50)|(b[:,0]>50);fa=a[:,1]>10;fb=b[:,1]>10;union=fa|fb
 return dict(excess_radiation_dose_relative_L1=float(abs(rb-ra).sum()/max(ra.sum(),1)),hot_union_velocity_error_m_s=float(np.sqrt((d[:,2:5]**2).sum(1))[active].mean()) if active.any() else None,predicted_temperature_below_absolute_zero_cells=int((b[:,0]<-273.15).sum()),temperature_MAE_C=float(d[:,0].mean()),hot_union_temperature_MAE_C=float(d[:,0][active].mean()) if active.any() else None,temperature_peak_C=[float(a[:,0].max()),float(b[:,0].max())],HRRPUV_MAE_kW_m3=float(d[:,1].mean()),flame_proxy_IoU=float((fa&fb).sum()/union.sum()) if union.any() else None,velocity_vector_MAE_m_s=float(np.sqrt((d[:,2:5]**2).sum(1)).mean()),radiation_intensity_MAE_kW_m2=float(d[:,5].mean()),integrated_HRR_dose_relative_error=float(abs(a[:,1].sum()-b[:,1].sum())/max(a[:,1].sum(),1)),temperature_peak_map_MAE_C=float(abs(a[:,0].max(0)-b[:,0].max(0)).mean()))
def main():
 f=json.loads((ROOT/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in f['files'].items())
 rows=[]
 for c in json.loads((ROOT/'cases.json').read_text()):
  if c['split']!='test':continue
  truth,t=load(c);target=np.arange(0,181,2);idx=abs(t[:,None]-target).argmin(0);a=np.array(truth[idx]);assert max(abs(t[idx]-target))<.3
  for name in ['cnn_8','cnn_16','cnn_32','interpolation_8','interpolation_16','interpolation_32']:
   b=np.load(ROOT/'data/predictions'/f"{name}_{c['case']}.npy");rows.append(dict(case=c['case'],model=name,wind_speed=c['wind_speed'],angle_deg=c['angle_deg'],ten_second_smoothed=metrics(uniform_filter1d(a,size=5,axis=0,mode='nearest'),uniform_filter1d(b,size=5,axis=0,mode='nearest'),a[0,5]),post_source=metrics(a[11:],b[11:],a[0,5]),**metrics(a,b)))
 report=dict(cases=rows,original_freeze_verified=True,flame_definition='HRRPUV >10 kW/m3, diagnostic combustion mask, not a visible flame rendering',radiation='integrated intensity, not directional incident surface flux',limitations='One fixed generic particle canopy; fixed moisture, no embers. 6 held-out simulations, one training seed; no real-world validation. Reference frames within0.3s of requested times.')
 (ROOT/'results/test-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
 main()
 from audit_pilot_corners import main as audit_corners
 audit_corners()
