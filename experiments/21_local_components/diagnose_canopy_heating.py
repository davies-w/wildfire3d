"""Read saved particle bounds and fds2ascii plume evidence; propose, never run, a correction."""
import json,subprocess,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'data/canopy_diagnosis';OUT.mkdir(exist_ok=True)
name='a21_single';dest=OUT/'single_T_10_20.csv'
if not dest.exists():
 answer=f'{name}\n2\n1\nn\n10 20\n1\n1\n{dest}\n'
 p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=ROOT/'data/cloud'/name,input=answer,text=True,capture_output=True,check=True,timeout=90);(OUT/'fds2ascii.log').write_text(p.stdout+p.stderr)
particles={}
for name in ['a21_single','a21_double','a21_corner','a21_double_fine']:
 p=ROOT/'data/cloud'/name/(name+'_1.prt5.bnd');lines=p.read_text().splitlines();i=0;best=[dict(max_C=-1,time_s=None) for _ in range(4)]
 while i<len(lines):
  t=float(lines[i].split()[0]);i+=1
  for c in range(4):
   nq,n=map(int,lines[i].split());i+=1;lo,hi=map(float,lines[i].split());i+=nq
   if n and hi>best[c]['max_C']:best[c]=dict(max_C=hi,time_s=t)
 particles[name]=dict(sampled_particle_maxima=best,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
v=np.loadtxt(dest,delimiter=',',skiprows=2);x,z,T=v.T;mask=(z>=3)&(z<=10)&(abs(x-11)<=2*(1-(z-3)/7))
report=dict(particle_class_order=['foliage','small roundwood','medium roundwood','large roundwood'],particle_output_sampling_fraction=.1,particle_output_interval_s=5,particles=particles,slice=dict(plane_y_m=12,averaging_s=[10,20],canopy_midplane_mean_C=float(T[mask].mean()),canopy_midplane_max_C=float(T[mask].max()),hottest_x_at_canopy_base_m=float(v[z==3][np.argmax(T[z==3]),0]),canopy_center_x_m=11,canopy_base_m=3),diagnosis='Insufficient canopy heating; plume bypass consistent with downstream deflection. Not a material validation.',limitations=['Only y=12 plane saved, not a3D plume volume.','Displayed-particle bounds cover approximately10% of particles at5 s intervals.','Tiny reactions are not excluded.','Material parameters, mesh and fuel distribution remain unvalidated.'],proposed_test=dict(case='a21_single_upstream',status='NOT_RUN',change='Move2x2 m ground ignition patch center from x11 to x8.5, y12 unchanged; all physics/materials otherwise unchanged.',reason='Offset by observed2.5 m downstream plume displacement at canopy-base height.',instrumentation='All particles saved every1 s; local gas/particle diagnostics and per-class mass flux; retain raw slices/boundaries.',horizon_s=180,cell_m=.5,source_kw=4000,source_duration_s=20,success='At least100 kW total HRR throughout40–50 s and at least1 MJ released over40–60 s, after source shutdown21 s; check vegetation fuel release and distinguish any building contribution. Engineering gate, not a universal ignition definition.',next_if_success='Request a matched shifted-source bare control before attributing building heating to vegetation; no automatic run.',budget=dict(expected_usd=[.03,.08],proposed_allowance_usd=.15,compute_rate_ceiling_usd_per_vm_hour=.08,one_worker_hour_reserved=True,ancillary_reserve_usd=.07,requires_new_authorization=True)))
(ROOT/'results/canopy-heating-diagnosis.json').write_text(json.dumps(report,indent=2))
fig,ax=plt.subplots(figsize=(10,6),layout='constrained');xx=np.unique(x);zz=np.unique(z);grid=T.reshape(len(zz),len(xx));im=ax.pcolormesh(xx,zz,grid,shading='nearest',cmap='inferno',vmin=20,vmax=300)
ax.add_patch(Polygon([(9,3),(13,3),(11,10)],closed=True,fill=False,edgecolor='#5be58c',lw=2));ax.add_patch(Rectangle((16,0),.5,6,facecolor='#c4b199',edgecolor='white'));ax.add_patch(Rectangle((10,0),2,.13,facecolor='orange'));ax.add_patch(Rectangle((7.5,.18),2,.13,fill=False,edgecolor='cyan',ls='--',lw=2))
ax.annotate('Canopy envelope',(10,7),(3,9),color='#5be58c',arrowprops=dict(arrowstyle='->',color='#5be58c'));ax.annotate('Existing ground burner',(11,.15),(11.8,1.5),color='white',arrowprops=dict(arrowstyle='->',color='white'));ax.annotate('Proposed burner position\n(not simulated)',(8.5,.3),(1,2),color='cyan',arrowprops=dict(arrowstyle='->',color='cyan'))
ax.set(xlim=(0,20),ylim=(0,12),xlabel='Downwind x (m)',ylabel='Height (m)',title='Existing single-canopy run: mean gas temperature, 10–20 s\ny = 12 m slice extracted with fds2ascii; no new simulation');fig.colorbar(im,ax=ax,label='Gas temperature (°C; colour scale capped at300)');fig.savefig(ROOT/'results/canopy-plume-diagnosis.png',dpi=150)
print(json.dumps(report['slice']))
