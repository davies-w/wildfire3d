"""Known-material 1-D wall response diagnostic, using measured heating only here.
20 mm generic wood; insulated back is an explicit approximation.
"""
import json
import numpy as np
from scene import ROOT
import component_model as m

def surface_temperature(profile,rad_excess,conv,ambient):
 dx=.02/profile.shape[1];conductance=2*.12/dx/1000;eps=.9;sigma=5.670374419e-11
 ts=profile[:,0].copy()
 for _ in range(8):
  residual=conductance*(ts-profile[:,0])-eps*(rad_excess+ambient-sigma*(ts+273.15)**4)-conv
  ts-=residual/(conductance+4*eps*sigma*(ts+273.15)**3)
 return ts

def advance(profile,rad_excess,conv,ambient,dt=.5):
 # Finite volumes,20 cells; same k,rho,cp as the deck. Radiation is incoming,
 # convection is already signed net flux. All flux inputs are kW/m2.
 k=.12;rho_cp=500*1700;dx=.02/profile.shape[1];eps=.9;sigma=5.670374419e-11
 p=profile.copy();steps=5;sub=dt/steps
 for _ in range(steps):
  face=k*np.diff(p,axis=1)/dx
  net=np.zeros_like(p);net[:,:-1]+=face;net[:,1:]-=face
  ts=surface_temperature(p,rad_excess,conv,ambient)
  net[:,0]+=2*k/dx*(ts-p[:,0])
  p+=sub*net/(rho_cp*dx)
 return p

def response(heat,ambient):
 p=np.full((heat.shape[1],20),20.);out=[p[:,0].copy()]
 for h in heat[:-1]:p=advance(p,h[:,0],h[:,1],ambient);out.append(surface_temperature(p,h[:,0],h[:,1],ambient))
 return np.array(out)

def main():
 rows=[]
 for name in ['b21_single_1','b21_single_2','b21_combined_0','b21_corner_1','b21_single_validation']:
  c=m.series(json.loads((ROOT/'data/component_states'/f'{name}.json').read_text()));b=np.array([n['kind']=='building' for n in c['g']['nodes']]);temp=response(c['heat'][:,b],c['ambient'][b]);actual=c['state'][:,b,0];a=np.flatnonzero(temp.max(1)>=350);r=np.flatnonzero(actual.max(1)>=350)
  rows.append(dict(case=name,split=c['split'],temperature_MAE_C=float(abs(temp-actual).mean()),predicted_peak_C=float(temp.max()),reference_peak_C=float(actual.max()),predicted_ignition_s=float(c['time'][a[0]]) if len(a) else None,reference_ignition_s=float(c['time'][r[0]]) if len(r) else None))
 (ROOT/'results/wall-response-diagnosis.json').write_text(json.dumps(dict(scope='Measured heating drives this diagnostic, so it is NOT autonomous graph inference. No parameters fitted. k=.12,rho=500,cp=1700,thickness=.02,emissivity=.9;20 finite volumes,0.1s steps,insulated-back approximation.',results=rows),indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
