from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;rows=[json.loads(p.read_text()) for p in sorted((R/'data').glob('x32_*.json'))];assert len(rows)==472;t=np.arange(0,181,2);fig,ax=plt.subplots(1,3,figsize=(15,4.5))
def band(axis,a,label,color):
 lo,med,hi=np.percentile(a,[10,50,90],axis=0);axis.fill_between(t,lo,hi,color=color,alpha=.16);axis.plot(t,med,label=label,color=color)
for key,label,color in [('HRR_kW','Gas-phase HRR','#bc4b2f'),('HRR_OX_kW','Solid oxidation HRR','#7259ad')]:band(ax[0],np.array([np.interp(t,r['hrr']['time_s'],r['hrr'][key]) for r in rows]),label,color)
band(ax[1],np.array([np.interp(t,r['temperature']['time_s'],r['temperature']['peak_C']) for r in rows]),'Peak gas temperature','#bc4b2f');ax[1].axhline(50,color='black',ls=':',label='HOT threshold 50°C')
mm=[]
for r in rows:
 a=np.array(r['material']['particle_mass_kg']);a[0]=r['initial_mass_kg'];mm.append(np.interp(t,r['material']['time_s'],a)/r['initial_mass_kg'])
band(ax[2],np.array(mm),'Particle mass / initial mass','#327c7a')
ax[0].set(yscale='symlog',ylim=(0,1e5),ylabel='Heat release (kW)');ax[1].set(ylabel='Temperature (°C)');ax[2].set(ylabel='Remaining mass fraction',ylim=(0,1.05))
for a in ax:a.axvspan(0,20.1,color='gray',alpha=.13);a.set_xlabel('Time (s)');a.grid(alpha=.2);a.legend(fontsize=8)
fig.suptitle('Original FDS outputs: 472 runs · median and 10–90% range · shaded: imposed ignition\nParticle mass loss includes moisture and reaction products; it is not all burned fuel',fontsize=11);fig.tight_layout();fig.savefig(R/'data/physics-audit.png',dpi=150)
