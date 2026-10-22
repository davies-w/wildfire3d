"""Prespecified exposed-surface metrics; fixed across model candidates and Stage C."""
import numpy as np

def metrics(reference,prediction,g):
 t=reference['time'];b=np.array([n['kind']=='building' for n in g['nodes']]);p=prediction['state'][:len(t),b,0];r=reference['state'][:,b,0];ph=prediction['heat'][:len(t),b];rh=reference['heat'][:,b]
 # Same positive-incident-dose definition as finish_stage_a.py: excess incoming
 # radiation over initial ambient, plus positive signed convective flux.
 pd=np.trapezoid(np.maximum(ph[:,:,0],0)+np.maximum(ph[:,:,1],0),t,axis=0);rd=np.trapezoid(np.maximum(rh[:,:,0],0)+np.maximum(rh[:,:,1],0),t,axis=0);exposed=rd>=100;relative=abs(pd-rd)/np.maximum(rd,100);mae=abs(p-r).mean(0);pi=np.flatnonzero(p.max(1)>=350);ri=np.flatnonzero(r.max(1)>=350)
 return dict(predicted_ignition=bool(len(pi)),reference_ignition=bool(len(ri)),predicted_ignition_s=float(t[pi[0]]) if len(pi) else None,reference_ignition_s=float(t[ri[0]]) if len(ri) else None,temperature_MAE_all_C=float(mae.mean()),exposed_surface_count=int(exposed.sum()),median_exposed_normalized_dose_error=float(np.median(relative[exposed])) if exposed.any() else None,p90_exposed_normalized_dose_error=float(np.quantile(relative[exposed],.9)) if exposed.any() else None,exposed_temperature_MAE_C=float(mae[exposed].mean()) if exposed.any() else None,absolute_dose_MAE_all_kj_m2=float(abs(pd-rd).mean()),per_patch=[dict(id=g['nodes'][j]['id'],exposed=bool(exposed[k]),predicted_dose_kj_m2=float(pd[k]),reference_dose_kj_m2=float(rd[k]),normalized_error=float(relative[k]),temperature_MAE_C=float(mae[k])) for k,j in enumerate(np.flatnonzero(b))],timing_note='Resampled0.5s temperature crossing for model comparison; raw FDS burning-rate/global-device checks remain authoritative for any-part ignition.')
