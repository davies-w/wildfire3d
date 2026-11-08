"""Plot raw 3D hot cells beside alternative diagnostic fits, not predictions."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from investigate_cone_pivot import R,OUT,evaluate
from preview_training import temperatures
r=json.loads((OUT/'report.json').read_text());case=r['cases'][0]['case'];row=next(x for x in r['cases'][0]['frames'] if x['active']);m=json.loads((R/'data/training-preview'/case/'metadata.json').read_text());domain=m['domain_m'];shape=tuple(np.rint(np.array(domain)/.5).astype(int));xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3)
p=next((R/'data/completed07').glob('*/'+case+'/solve/'+case+'_1_1.sf'));temp=next(a.reshape(-1) for t,a in temperatures(p,domain,.5) if t==row['time_s']);hot=np.flatnonzero(temp>50);keep=hot[np.linspace(0,len(hot)-1,min(2000,len(hot))).astype(int)]
fig=plt.figure(figsize=(13,5.5));axs=[]
for i,(key,label) in enumerate([('legacy','Original restricted fit'),('plus_horizontal_apex','Free apex + azimuth diagnostic')]):
 c=row['fits'][key];assert evaluate({k:v for k,v in c.items() if k!='seed_fits'},xyz,temp)['hot_recall']>=.95
 ax=fig.add_subplot(1,2,i+1,projection='3d');axs.append(ax);dots=ax.scatter(*xyz[keep].T,c=temp[keep],s=3,cmap='inferno',vmin=50,vmax=1500,alpha=.45)
 a=np.array(c['apex_m']);theta,phi=np.deg2rad([c['tilt_deg'],c['azimuth_deg']]);u=np.array([np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)]);v=np.cross(u,[0,1,0]);v=v/np.linalg.norm(v);w=np.cross(u,v);th=np.linspace(0,2*np.pi,65);rim=a+c['length_m']*u+c['radius_m']*(np.cos(th)[:,None]*v+np.sin(th)[:,None]*w)
 ax.plot(*rim.T,color='#1675bc',lw=1)
 for j in range(0,64,8):ax.plot(*np.array([a,rim[j]]).T,color='#1675bc',lw=.8)
 ax.scatter(*a,c='#1266a5',s=45,marker='x');ign=np.r_[m['tree_center_xy_m'],0]+m['static_inputs']['ignition_contact_relative_xyz_m'];ax.scatter(*ign,c='red',marker='*',s=70)
 ax.set(xlim=(-5,30),ylim=(-8,25),zlim=(0,35),xlabel='x (m)',ylabel='y (m)',zlabel='z (m)');ax.set_box_aspect((35,33,35));ax.view_init(22,-68)
 ax.set_title(f"{label}\nApex z={a[2]:.2f}m; {100*c['hot_precision']:.1f}% of enclosed cells hot\n{100*c['hot_recall']:.1f}% hot-cell coverage",fontsize=10)
fig.colorbar(dots,ax=axs,shrink=.55,pad=.02,label='Raw saved gas temperature (C)')
fig.suptitle(f'{case}: actual saved volume at {row["time_s"]:.3f} s',fontsize=12)
fig.text(.5,.025,'Dots: display subsample of raw >50 C cells (not interpolated). Blue wire: geometric cone; red star: ignition location.\nBoth fits use all hot cells for final calibration. Raw domain is24 x16 x32m; no gas outside it was observed. Diagnostic only.',ha='center',fontsize=9)
fig.savefig(OUT/'fit-comparison-3d.png',dpi=130);plt.close(fig)
lines=['# Cone pivot investigation','','Scope: both preview cases; all four active saved eucalyptus volumes. No bulk extraction, new simulations, model training or raw deletion.','', 'The ground apex is a constrained geometric fitting result, not an observed fire origin. Oak has no active source cone; its zeros are missing/inactive placeholders.','', '| Saved time (s) | Original z (m) | Dense-height z (m) | Free-azimuth z (m) | Free-apex xyz (m) | Original hot purity | Free-apex hot purity |','|---:|---:|---:|---:|---|---:|---:|']
for f in r['cases'][0]['frames']:
 if not f['active']:continue
 a=f['fits'];free=a['plus_horizontal_apex'];lines.append(f"| {f['time_s']:.3f} | {a['legacy']['apex_m'][2]:.2f} | {a['dense_height']['apex_m'][2]:.2f} | {a['plus_azimuth']['apex_m'][2]:.2f} | {', '.join(f'{v:.2f}' for v in free['apex_m'])} | {100*a['legacy']['hot_precision']:.1f}% | {100*free['hot_precision']:.1f}% |")
lines+=['','All listed fits preserve at least95% hot-cell coverage. Purity is the fraction of enclosed cells above50C; the remainder is cool air.','', 'Findings:','', '- None of the active eucalyptus hot cells are below12m. A fitted ground apex does not mean ground ignition.','- Exhaustive evaluation of the original80 height/tilt candidates reproduces the selected original fits. The top-eight shortcut is not responsible in these frames.','- Adding missing heights changes pivots but yields only modest volume improvements with the original10-degree tilt grid. Continuous tilt can reduce volume while retaining a nearly ground-level apex.','- Adding azimuth alone does not remove the near-ground preference for the first three frames.','- Freeing apex x/y substantially improves volume and purity, but drives x to the permitted upstream boundary. Expanding the x/y bounds moves the solution outside the raw domain. The apex is therefore sensitive to arbitrary bounds and is not a validated physical origin.','- The ignition-anchored fit is feasible at13.4m and captures95%, but is not consistently smallest by analytic cone volume. Minimum volume and physically meaningful apex are different objectives.','', 'Recommendation: do not bulk-extract the current pivot as a physical target. Choose explicit semantics before changing labels: a source-anchored cone (origin defined by ignition/geometry) versus a free spatial envelope (centre/axis/extents, no fire-origin claim). Adding azimuth alone is insufficient. A cone/frustum/ellipsoid comparison on a broader verified sample is needed before choosing a replacement.','', 'Limits: only one active-fire example here; oak is the inactive control. Search is numerical/coarse and not proven globally optimal. Hot gas is domain-clipped and50C is a diagnostic threshold, not a flame criterion. The pointed-cone shape, maximum axial length rule and95% recall objective remain assumptions. No training labels were overwritten.']
(OUT/'findings.md').write_text('\n'.join(lines)+'\n');print('Report and 3D comparison written')
