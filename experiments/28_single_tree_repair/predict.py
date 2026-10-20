"""Standalone inference: model weights + parameters only; no FDS data access."""
import argparse
import numpy as np
import torch
from original_cnn import CNN,prediction
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--wind',type=float,required=True);p.add_argument('--angle',type=float,required=True);p.add_argument('--times',default='0,20,40,60,90,120,180');p.add_argument('--out',required=True);a=p.parse_args()
t=np.array([float(v) for v in a.times.split(',')]);assert 1<=a.wind<=5 and np.all((t>=0)&(t<=180)),'Outside studied wind/time range'
m=CNN();m.load_state_dict(torch.load(a.model,map_location='cpu',weights_only=True));m.eval();c=dict(wind_speed=a.wind,angle_deg=a.angle%360);v=prediction(m,c,t);np.savez_compressed(a.out,time=t,fields=v,quantities=np.array(['temperature_C','HRRPUV_kW_m3','u_m_s','v_m_s','w_m_s','integrated_intensity_kW_m2']),extent=np.array([0,24,0,16,0,16]),cell_size_m=.5);print(v.shape)
