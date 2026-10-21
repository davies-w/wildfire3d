"""Align reference output times to frozen prediction times; never modifies predictions."""
import numpy as np

def align_reference(a,t,wanted):
 t=np.asarray(t);wanted=np.asarray(wanted);assert np.all(np.diff(t)>0) and np.all(np.diff(wanted)>0);assert wanted[0]>=t[0]-1e-5 and wanted[-1]<=t[-1]+1e-5
 nearest=float(np.min(abs(t[:,None]-wanted),axis=0).max());assert nearest<1.,nearest
 out=np.empty((len(wanted),*a.shape[1:]),dtype=np.float32)
 for k,v in enumerate(wanted):
  j=int(np.searchsorted(t,v));j=min(max(j,1),len(t)-1);w=float(np.clip((v-t[j-1])/(t[j]-t[j-1]),0,1));out[k]=a[j-1]*(1-w)+a[j]*w
 return out,dict(method='Linear interpolation of reference FDS frames onto frozen nominal prediction times; no prediction changes or extrapolation',maximum_nearest_reference_time_offset_s=nearest,raw_start_s=float(t[0]),raw_end_s=float(t[-1]))
