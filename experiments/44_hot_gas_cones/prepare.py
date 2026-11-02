from pathlib import Path
import hashlib,json,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Ellipse
from cones import fit,membership,metrics,ellipsoid,axis,THRESHOLD_C,COVERAGE
R=Path(__file__).resolve().parent
SOURCE=R.parent/'35_surrogate_diagnostics/attempt10'
OUT=R/'data';(OUT/'histories').mkdir(parents=True,exist_ok=True);(OUT/'plots').mkdir(exist_ok=True)
xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in (48,32,32)],indexing='ij'),-1).reshape(-1,3)
cases=json.loads((SOURCE/'cases.json').read_text());allcases=[];started=time.monotonic()
grid_indices=np.indices((48,32,32));boundary=np.any((grid_indices==0)|(grid_indices==np.array([47,31,31])[:,None,None,None]),axis=0)
for case in cases:
    name=case['case'];p=SOURCE/'data/fields'/f'{name}.npy';tp=p.with_name(name+'-time.npy')
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    fields=np.load(p,mmap_mode='r');times=np.load(tp);assert fields.shape==(91,6,48,32,32)
    rows=[];plot_frames={int(np.argmin(abs(times-t))) for t in [20,40,80,160]};panels=[]
    for i,t in enumerate(times):
        temp=np.asarray(fields[i,0],dtype=float).reshape(-1);hot=temp>THRESHOLD_C;c=fit(xyz[hot],case['crown_height_m'])
        row=dict(time_s=float(t),igniter_on=bool(t<20),domain_peak_temperature_C=float(temp.max()),active=bool(hot.any()))
        if c is None:row.update(cone=None,cone_metrics=None,ovoid_metrics=None)
        else:
            volume,h,tilt,length,radius=c;mask=membership(xyz,h,tilt,length,radius);oval,center,cov=ellipsoid(xyz,hot,temp)
            assert mask.any()
            ev,v=np.linalg.eigh(cov);d=xyz-center;dist=np.sum((d@v)**2/np.maximum(ev,1e-12),axis=1);k=int(np.ceil(COVERAGE*hot.sum()));cut=float(np.partition(dist[hot],k-1)[k-1]);oval95=dist<=cut+1e-9
            row.update(cone=dict(pivot_height_m=h,tilt_from_vertical_deg=tilt,length_m=length,end_radius_m=radius,peak_temperature_C=float(temp[mask].max())),
                       cone_metrics=metrics(mask,hot),ovoid_metrics=metrics(oval,hot),ovoid95_metrics=metrics(oval95,hot),
                       temperature_excess_capture=float(np.sum(np.maximum(temp[mask&hot]-20,0))/np.sum(temp[hot]-20)),
                       analytic_cone_volume_m3=float(volume),in_domain_cone_volume_m3=float(mask.sum()*.125),
                       apex_below_crown=bool(h<2),peak_temperature_missed_C=float(temp.max()-temp[mask].max()),
                       hot_cells_on_domain_boundary=int(hot.reshape(48,32,32)[boundary].sum()))
            assert row['cone_metrics']['hot_recall']>=COVERAGE-1e-9
        rows.append(row)
        if i in plot_frames:panels.append((temp.reshape(48,32,32).max(axis=1).T.copy(),row,c,center if c else None,cov if c else None))
    result=dict(case=name,conditions=case,input_sha256=sha,time_sha256=hashlib.sha256(tp.read_bytes()).hexdigest(),snapshots=rows)
    (OUT/'histories'/f'{name}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');allcases.append(result)
    fig,axs=plt.subplots(1,4,figsize=(18,5),sharex=True,sharey=True)
    for ax,(field,row,c,center,cov) in zip(axs,panels):
        im=ax.imshow(field,origin='lower',extent=[0,24,0,16],vmin=20,vmax=1000,cmap='inferno',aspect='equal')
        ax.contour(np.arange(.25,24,.5),np.arange(.25,16,.5),field,levels=[50],colors=['cyan'],linewidths=.6)
        ax.add_patch(Polygon([[6.5,2],[9.5,2],[8,2+case['crown_height_m']]],fill=False,edgecolor='lime',linewidth=1))
        if c:
            _,h,tilt,L,r=c;u=axis(tilt)[[0,2]];perp=np.array([u[1],-u[0]]);apex=np.array([8,h]);tip=apex+L*u
            ax.add_patch(Polygon([apex,tip+r*perp,tip-r*perp],fill=False,edgecolor='white',linewidth=1.5))
            ev,v=np.linalg.eigh(cov[np.ix_([0,2],[0,2])]);angle=np.degrees(np.arctan2(v[1,1],v[0,1]));ax.add_patch(Ellipse(center[[0,2]],4*np.sqrt(max(ev[1],0)),4*np.sqrt(max(ev[0],0)),angle=angle,fill=False,edgecolor='#ff80ff',linestyle='--'))
            m=row['cone_metrics'];ax.set_title(f"{row['time_s']:.1f}s · peak {row['cone']['peak_temperature_C']:.0f}°C\nHot captured {m['hot_recall']:.0%}; purity {m['hot_precision']:.0%}")
        else:ax.set_title(f"{row['time_s']:.1f}s · no gas >50°C")
        ax.set(xlim=(0,24),ylim=(0,16),xlabel='x (m)')
    axs[0].set_ylabel('Height (m)');fig.colorbar(im,ax=axs,shrink=.65,label='Maximum gas temperature through y (°C); clipped at 1000')
    fig.suptitle(f"{name}: wind +x {case['wind_speed']} m/s; crown height {case['crown_height_m']} m\nWhite cone; magenta original 2σ oval; cyan >50°C; green crown. Side view, NOT a flame boundary.",fontsize=11)
    fig.text(.08,.04,'0.5 m grid; 3 m-wide crown above 2 m; imposed 1500°C igniter for 20 s; no trunks/buildings/embers. Instantaneous saved fields.',fontsize=9)
    fig.savefig(OUT/'plots'/f'{name}.png',dpi=110);plt.close(fig)
    print(name,len(allcases),round(time.monotonic()-started),flush=True)
active=[r for c in allcases for r in c['snapshots'] if r['active']]
def summary(rows):
    return dict(frames=len(rows),cone_recall_median=float(np.median([r['cone_metrics']['hot_recall'] for r in rows])),cone_precision_median=float(np.median([r['cone_metrics']['hot_precision'] for r in rows])),cone_iou_median=float(np.median([r['cone_metrics']['iou'] for r in rows])),ovoid_recall_median=float(np.median([r['ovoid_metrics']['hot_recall'] for r in rows])),ovoid_iou_median=float(np.median([r['ovoid_metrics']['iou'] for r in rows])),ovoid95_recall_median=float(np.median([r['ovoid95_metrics']['hot_recall'] for r in rows])),ovoid95_precision_median=float(np.median([r['ovoid95_metrics']['hot_precision'] for r in rows])),ovoid95_iou_median=float(np.median([r['ovoid95_metrics']['iou'] for r in rows])),apex_below_crown_fraction=float(np.mean([r['apex_below_crown'] for r in rows])),peak_missed_frames=sum(r['peak_temperature_missed_C']>1e-6 for r in rows))
report=dict(cases=len(allcases),snapshots=sum(len(c['snapshots']) for c in allcases),active=summary(active),after_igniter=summary([r for r in active if not r['igniter_on']]),hot_threshold_C=THRESHOLD_C,requested_hot_coverage=COVERAGE,method='Minimum analytic cone volume among coarse-grid candidates; top eight sample-ranked candidates recalibrated on all hot cell centers',time_definition='Instantaneous saved frames, not maxima over the intervening approximately two seconds',shape_definition='Apex (8,8,h); circular cone axis in +x/z plane; 0..90 degree tilt; apex ground or seven heights within crown; no targets',limitations=['50°C is a diagnostic threshold, not ignition','95% cell-count coverage is a fit constraint, not an out-of-sample prediction','Analytic cone may extend outside saved domain; metrics only inside domain','Source includes imposed igniter and hot gas, not isolated tree combustion','No heat flux, radiative field, ember hazard, or within-interval maximum inferred','48 previously examined development histories, no new simulations or neural training'])
(OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'index.json').write_text(json.dumps([dict(case=c['case'],conditions=c['conditions'],snapshots=c['snapshots']) for c in allcases])+'\n')
print(json.dumps(report,indent=2))
