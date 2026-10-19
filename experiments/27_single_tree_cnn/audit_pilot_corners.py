"""Previously inspected pilot corners: diagnostic only, never untouched-test evidence."""
import json,numpy as np,torch
from cnn import ROOT,CNN,load,prediction

def main():
 rows=[]
 for n in [8,16,32]:
  m=CNN();m.load_state_dict(torch.load(ROOT/'data/models'/f'cnn_{n}.pt',map_location='cpu',weights_only=True));m.eval()
  for c in [c for c in json.loads((ROOT/'cases.json').read_text()) if c['split']=='pilot']:
   a,t=load(c);idx=t>=21;truth=np.array(a[idx]);b=prediction(m,c,t[idx]);active=(truth[:,0]>50)|(b[:,0]>50);fa=truth[:,1]>10;fb=b[:,1]>10;union=fa|fb
   rows.append(dict(case=c['case'],training_cases=n,times_s=t[idx].tolist(),hot_temperature_MAE_C=float(abs(b[:,0]-truth[:,0])[active].mean()) if active.any() else None,combustion_mask_IoU=float((fa&fb).sum()/union.sum()) if union.any() else None,predicted_snapshot_peak_C=float(b[:,0].max()),FDS_snapshot_peak_C=float(truth[:,0].max())))
 report=dict(cases=rows,scope='Known calibration corners, excluded from fitting and checkpoint selection, NOT untouched tests. Only five post-source volume snapshots at36s intervals; no full-time peak/dose claim. Audit performed after prediction freeze; no model changes based on it.')
 (ROOT/'results/pilot-corner-audit.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
