"""Straight-line obstruction mask for building boxes; not a smoke/plume solver."""
import numpy as np

def clear_segments(receivers,senders,boxes):
 # Segment interior only; endpoints lie on surfaces. No attenuation by vegetation.
 start=np.asarray(senders)[None,:,:];end=np.asarray(receivers)[:,None,:];direction=end-start;clear=np.ones(direction.shape[:2],dtype=bool)
 for box in boxes:
  lo=np.full(direction.shape[:2],-np.inf);hi=np.full(direction.shape[:2],np.inf);valid=np.ones(direction.shape[:2],dtype=bool)
  for axis in range(3):
   low,high=box[2*axis:2*axis+2];d=direction[:,:,axis];o=start[:,:,axis];parallel=abs(d)<1e-12
   valid &= ~parallel | ((o>=low+1e-6)&(o<=high-1e-6))
   safe=np.where(parallel,1,d);a=(low+1e-6-o)/safe;b=(high-1e-6-o)/safe
   lo=np.maximum(lo,np.where(parallel,-np.inf,np.minimum(a,b)));hi=np.minimum(hi,np.where(parallel,np.inf,np.maximum(a,b)))
  blocked=valid&(np.maximum(lo,1e-5)<np.minimum(hi,1-1e-5));clear &= ~blocked
 return clear

def apply(g,c):
 boxes=c.get('building_boxes')
 if boxes is None:
  f=c['facade'];boxes=[[f['x'],f['x']+.5,*f['y'],*f['z']]]
  if c.get('family')=='corner':boxes.append([24,30,16,16.5,0,6])
  if c.get('roof_box_m'):boxes.append(c['roof_box_m'])
 xyz=np.array([n['xyz'] for n in g['nodes']]);mask=clear_segments(xyz,xyz,boxes);g['kernel']=g['kernel']*mask;g.pop('_wind_kernel',None)
 g['occlusion']='Building-box straight line masking, no vegetation/smoke attenuation; does not model transported flame paths.'
 return g

if __name__=='__main__':
 box=[[0,1,0,1,0,1]]
 assert not clear_segments([[2,.5,.5]],[[-1,.5,.5]],box)[0,0]
 assert clear_segments([[2,2,.5]],[[-1,2,.5]],box)[0,0]
 assert clear_segments([[0,.5,.5]],[[-1,.5,.5]],box)[0,0]
 print('Segment obstruction checks passed')
