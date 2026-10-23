import json,urllib.request,urllib.parse
from pathlib import Path
import numpy as np,torch
from original_cnn import cond
from geometry_model import features
R=Path(__file__).parent
PREFIX='diagnostics35/attempt05/'
def upload(n,data):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(req,timeout=20))['access_token'];url='https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+n,safe='');urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST'),timeout=180).read()
def inputs(c,t,g):
 return torch.from_numpy(np.concatenate([cond(c,t),np.repeat(features(g)[None],len(t),0),np.full((len(t),1),(c['moisture']-.12)/.18,np.float32)],1)).cuda()
