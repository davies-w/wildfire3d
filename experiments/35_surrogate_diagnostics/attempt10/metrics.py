"""Per-frame sufficient statistics and configuration-balanced full-history summaries."""
import torch,numpy as np
from model import physical,channel_losses
NAMES=['T','HRR','u','v','w','radiation']
def statistics(p,y,truth,w,scales):
 obj,whole=channel_losses(p,y,scales);a=physical(p,w);err=(a-truth).abs();axes=(1,2,3);hot=truth[:,0]>50;predhot=a[:,0]>50;burn=truth[:,1]>.01
 extra=torch.stack([(err[:,0]*hot).sum(axes),((truth[:,0]-20).abs()*hot).sum(axes),hot.sum(axes),(err[:,1]*burn).sum(axes),(truth[:,1].abs()*burn).sum(axes),burn.sum(axes),a[:,1].sum(axes)*.125,truth[:,1].sum(axes)*.125,(hot&predhot).sum(axes),((~hot)&predhot).sum(axes),(hot&(~predhot)).sum(axes),(p[:,1]<0).float().mean(axes),(p[:,1]>10).float().mean(axes)],1)
 return torch.cat([obj,whole,err.mean((2,3,4)),extra],1).cpu().numpy()
def summarize_case(v,t):
 out={}
 def div(a,b):return float(a/b) if b>0 else None
 for name,mask in [('all',t>=0),('ignition',t<=20.1),('post_source',t>=21),('active_window', (t>=21)&(t<81)),('late',t>=120)]:
  q=v[mask];ts=t[mask];s=q.sum(0);tp,fp,fn=s[26:29];trap=(getattr(np,'trapezoid',None) or getattr(np,'trapz'))
  out[name]=dict(objective_MSE=float(q[:,:6].mean()),channel_objective_MSE=q[:,:6].mean(0).tolist(),whole_normalized_MSE=q[:,6:12].mean(0).tolist(),channel_physical_MAE=q[:,12:18].mean(0).tolist(),hot_temperature_MAE_C=div(s[18],s[20]),hot_temperature_relative_L1_percent=div(100*s[18],s[19]),burning_HRR_MAE_kWm3=div(s[21],s[23]),burning_HRR_relative_L1_percent=div(100*s[21],s[22]),total_HRR_relative_L1_percent=div(100*np.abs(q[:,24]-q[:,25]).sum(),s[25]),total_HRR_MAE_kW=float(np.abs(q[:,24]-q[:,25]).mean()),energy_pred_kJ=float(trap(q[:,24],ts)),energy_truth_kJ=float(trap(q[:,25],ts)),hot_precision=div(tp,tp+fp),hot_recall=div(tp,tp+fn),hot_f1=div(2*tp,2*tp+fp+fn),negative_encoded_HRR_fraction=float(q[:,29].mean()),upper_clipped_HRR_fraction=float(q[:,30].mean()))
 return out

def aggregate(rows,cases,ids):
 result={};configs=sorted({cases[i]['configuration'] for i in ids})
 for window in rows[ids[0]]:
  result[window]={}
  for key in rows[ids[0]][window]:
   vals=[]
   for cfg in configs:
    values=[rows[i][window][key] for i in ids if cases[i]['configuration']==cfg and rows[i][window][key] is not None]
    if values:vals.append(np.mean(values,axis=0))
   result[window][key]=np.mean(vals,axis=0).tolist() if vals else None
 result['configurations']=len(configs);return result
