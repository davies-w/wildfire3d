from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'data/cloud/campaign.json').read_text());b=s['bracket']
if not b:raise RuntimeError('No threshold bracket')
fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
colors={'full':'black','wide':'#0072B2','tight':'#009E73','mixed':'#D55E00','combined':'#CC79A7'}
for i,key in enumerate(['nonigniting','igniting']):
    ref=b[key];runs=[ref]+[r for r in s['results'] if r['phase']=='compare' and r['power_kw_m2']==ref['power_kw_m2'] and r['full_horizon']]
    for r in runs:
        with (ROOT/'data/cloud'/r['case']/(r['case']+'_devc.csv')).open() as f:
            it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];arr=np.array([list(map(float,row)) for row in it if row])
        for j,q in enumerate(['house_max','house_flux_max']):axes[i,j].plot(arr[:,0],arr[:,keys.index(q)],label=r['mode'],color=colors[r['mode']])
    axes[i,0].axhline(350,color='gray',ls='--');axes[i,0].set_ylabel(f"{key}: {ref['power_kw_m2']:.1f} kW/m²\nHouse max temperature (°C)")
    axes[i,1].set_ylabel('House max gauge heat flux (kW/m²)')
    axes[i,2].bar([r['mode'] for r in runs],[(r['cpu_user_s']+r['cpu_system_s'])/60 for r in runs],color=[colors[r['mode']] for r in runs]);axes[i,2].set_ylabel('Aggregate CPU minutes / 90 s scenario');axes[i,2].tick_params(axis='x',rotation=30)
    for j in (0,1):axes[i,j].set_xlabel('Simulated seconds');axes[i,j].legend(fontsize=8)
fig.suptitle('Particle vegetation: domain and mesh comparisons near the model ignition threshold')
fig.savefig(ROOT/'results/comparison.png',dpi=160)
