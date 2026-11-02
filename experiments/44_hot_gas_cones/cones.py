"""Deterministic geometric compression, not neural training or a fire solver."""
import numpy as np

THRESHOLD_C = 50.0
COVERAGE = .95

def axis(tilt):
    a=np.deg2rad(tilt)
    return np.array([np.sin(a),0.,np.cos(a)])

def membership(xyz, h, tilt, length, radius):
    d=xyz-np.array([8.,8.,h]);u=axis(tilt);s=d@u
    radial2=np.maximum(np.sum(d*d,axis=1)-s*s,0)
    return (s>=0)&(s<=length+1e-9)&(radial2 <= (radius*s/length)**2+1e-9)

def candidate(points,h,tilt):
    d=points-np.array([8.,8.,h]);s=d@axis(tilt);positive=s>1e-8
    k=int(np.ceil(COVERAGE*len(points)))
    if positive.sum()<k:return None
    s=s[positive];d=d[positive];length=float(s.max())
    slopes=np.sqrt(np.maximum(np.sum(d*d,axis=1)-s*s,0))/s
    radius=float(np.partition(slopes,k-1)[k-1]*length)
    return (np.pi*radius**2*length/3,float(h),float(tilt),length,radius)

def fit(points,crown_height):
    if not len(points):return None
    # Deterministic subsampling ranks candidates only. Final dimensions use all hot cells.
    sample=points if len(points)<=1024 else points[np.sort(np.random.default_rng(3516).choice(len(points),1024,replace=False))]
    candidates=[]
    for h in np.unique(np.r_[0.,np.linspace(2.,2.+crown_height,7)]):
        for tilt in range(0,91,10):
            c=candidate(sample,h,tilt)
            if c is not None:candidates.append(c)
    candidates.sort()
    final=[candidate(points,c[1],c[2]) for c in candidates[:8]]
    final=[c for c in final if c is not None]
    # Ground-level upright apex is always feasible for this positive-z grid.
    if not final:final=[candidate(points,0.,0.)]
    return min(final)

def metrics(pred,hot):
    tp=int(np.count_nonzero(pred&hot));p=int(pred.sum());n=int(hot.sum());union=int(np.count_nonzero(pred|hot))
    return dict(hot_cells=n,enclosed_cells=p,covered_hot_cells=tp,hot_recall=tp/n if n else None,
                hot_precision=tp/p if p else None,iou=tp/union if union else None,
                missed_hot_cells=n-tp,cool_cells_included=p-tp)

def ellipsoid(xyz,hot,temp):
    w=np.where(hot,temp-20.,0.);c=np.sum(xyz*w[:,None],axis=0)/w.sum();d=xyz-c
    cov=(d.T*w)@d/w.sum();ev,vec=np.linalg.eigh(cov)
    # Explicit numerical floor far below a grid cell, only for singular covariance.
    distance=np.sum((d@vec)**2/np.maximum(ev,1e-12),axis=1)
    return distance<=4.,c,cov
