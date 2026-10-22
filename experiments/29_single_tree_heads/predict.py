"""Standalone prediction: weights and conditions only, no simulation arrays."""
import argparse
import numpy as np
import torch
from models import Model
from original_cnn import prediction
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--kind',choices=['bounded','heads'],required=True);p.add_argument('--wind',type=float,required=True);p.add_argument('--angle',type=float,required=True);p.add_argument('--out',required=True);a=p.parse_args();m=Model(a.kind);m.load_state_dict(torch.load(a.model,map_location='cpu',weights_only=True));m.eval();times=np.arange(0,181,2,dtype=float);assert 1<=a.wind<=5;fields=prediction(m,dict(wind_speed=a.wind,angle_deg=a.angle),times);np.savez_compressed(a.out,time_s=times,fields=fields);print(fields.shape)
