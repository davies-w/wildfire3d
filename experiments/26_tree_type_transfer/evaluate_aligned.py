"""One-shot held-out comparison, only after checking the prediction freeze."""
import json,hashlib
import numpy as np
from build import ROOT,CLASSES
from model_data import geometry
from extract import extract

def main():
 freeze=json.loads((ROOT/'results/prediction-freeze.json').read_text())
 for path,h in freeze['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 cs=[c for c in json.loads((ROOT/'cases.json').read_text()) if c['case'] in freeze['cases']];reports=[]
 for c in cs:
  raw_report=extract(c);g=geometry(c);a=np.load(ROOT/'data/extracted'/(c['case']+'.npz'));tt=a['time'];raw=a['state'].reshape(len(tt),-1,6)[:,g['indices']];truth=np.stack([(raw[:,:,0]-20)/1000,raw[:,:,1]/g['static'][:,9].numpy()],-1)
  for label in ['single_composed','pair_adapted','independent_additive']:
   p=np.load(ROOT/'data/predictions'/f"{c['case']}__{label}.npz");target_time=p['time'].astype(float)
   assert target_time[0]>=a['time'][0] and target_time[-1]<=a['time'][-1], 'No extrapolation'
   original=a['state'].reshape(len(a['time']),-1,6)[:,g['indices']]
   raw=np.stack([np.interp(target_time,a['time'],original[:,j,k]) for j in range(original.shape[1]) for k in range(6)],axis=1).reshape(len(target_time),original.shape[1],6)
   tt=target_time;truth=np.stack([(raw[:,:,0]-20)/1000,raw[:,:,1]/g['static'][:,9].numpy()],-1)
   dt=np.diff(tt);metrics=[]
   for i,t in enumerate(c['trees']):
    mask=p['instance']==i;temp=p['state'][:,mask,0]*1000+20;actual=raw[:,mask,0];diff=abs(temp-actual);active=(temp>100)|(actual>100)
    heat=p['heat'][:,mask];actual_heat=raw[:-1,mask][:,:,[2,3]]
    doses={}
    for j,q in enumerate(['incident_radiation','convection']):
     pred=(heat[:,:,j]*dt[:,None]).sum(0);target=(actual_heat[:,:,j]*dt[:,None]).sum(0)
     doses[q]=dict(mean_absolute_dose_error_kJ_m2=float(abs(pred-target).mean()),relative_L1_error=float(abs(pred-target).sum()/max(abs(target).sum(),1e-6)))
    fuel_pred=float((p['rate'][:,mask].sum(1)*dt).sum());fuel_true=raw_report['canopies'][i]['fuel_release_after_heater_kg']
    after=tt[:-1]>=c['duration']+1;fuel_after=float((p['rate'][after][:,mask].sum(1)*dt[after]).sum())
    metrics.append(dict(type=t['type'],temperature_MAE_C=float(diff.mean()),active_union_temperature_MAE_C=float(diff[active].mean()) if active.any() else None,mass_fraction_MAE=float(abs(p['state'][:,mask,1]-truth[:,mask,1]).mean()),heat_flux_MAE_kW_m2=float(abs(heat-actual_heat).mean()),dose=doses,predicted_post_heater_fuel_kg=fuel_after,FDS_post_heater_fuel_kg=fuel_true))
   reports.append(dict(case=c['case'],family=c['family'],split=c['split'],model=label,canopies=metrics))
 (ROOT/'results/test-summary.json').write_text(json.dumps(dict(frozen_hashes_verified=len(freeze['files']),comparisons=reports,limitations=['Two C-pair tests, one AA familiar pair, with matched source-removal controls','Generic fixed-instance geometries and chemistry; C has more fuel at same bulk density','Regional canopy outputs only; gas, ground and flame fields not predicted by this prototype','Whole configuration holdouts; no statistical confidence from this tiny set','Source removal changes flow/shielding; not exact linear attribution'],timestamp_alignment='FDS output occurs on adaptive solver steps, up to roughly0.1s after nominal2s samples. Linearly interpolate observed regional states/fluxes onto frozen prediction times; no extrapolation or prediction changes. Original evaluator preserved and freeze-verified.',aggregation='Unweighted spatial-region/fuel-class errors; active temperature union above100C. Heat dose separately integrates incident radiation and convection; not net absorbed radiation.'),indent=2))
 import subprocess
 p=subprocess.run([str(ROOT.parents[1]/'.venv/bin/dvc'),'commit','-f','experiment'],cwd=ROOT,capture_output=True,text=True)
 (ROOT/'results/provenance.log').write_text(p.stdout+p.stderr)
 assert p.returncode==0,'DVC provenance failed; preserve all outputs and inspect provenance.log'
 print('TEST EVALUATION COMPLETE',flush=True)
if __name__=='__main__':main()
