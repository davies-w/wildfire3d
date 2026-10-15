"""Render registered observations for visual QA, never infer fire outcomes from colors."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'results/properties.json').read_text())
fig,axes=plt.subplots(3,4,figsize=(14,11),layout='constrained')
for ax,entry in zip(axes.flat,entries):
    a=np.load(ROOT/'data/scenes'/entry['id']/'geometry.npz')
    image=ax.imshow(a['dsm']-a['dem'],extent=(0,120,0,120),vmin=0,vmax=25,cmap='viridis')
    ax.contour(a['main_building'],levels=[0.5],extent=(0,120,0,120),origin='upper',colors=['white'],linewidths=1)
    ax.set_title(entry['id'],fontsize=10);ax.set_xlabel('East (m)');ax.set_ylabel('North (m)')
fig.colorbar(image,ax=axes.ravel().tolist(),label='Observed height above terrain (m)',shrink=0.75)
fig.suptitle('12 Sonoma candidate buildings — white outlines identify selected structures\n2022 LiDAR; building dates vary; species and materials unverified',fontsize=14)
fig.savefig(ROOT/'results/geometry_qa.png',dpi=150)
plt.close(fig)
