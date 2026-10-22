import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scene import ROOT,cases,deck
src=ROOT.parent/'14_ignition_surrogate';names=['sebastopol_10','sebastopol_11'];tests=['santa_rosa_east_03','glen_ellen_06'];inventory=json.loads((src/'results/properties.json').read_text());lookup={r['id']:r for r in inventory}
for a in names:
 for b in tests:
  u=lookup[a]['extent_utm_m'];v=lookup[b]['extent_utm_m'];assert u[2]<v[0] or v[2]<u[0] or u[3]<v[1] or v[3]<u[1]
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained');evidence=[]
for ax,name in zip(axes,names):
 p=src/'data/scenes'/name/'geometry.npz';a=np.load(p);im=ax.imshow(a['canopy'],vmin=0,vmax=25,cmap='YlGn',extent=(0,120,0,120));ax.contour(a['main_building'],levels=[.5],extent=(0,120,0,120),origin='upper',colors='red');ax.set_title(name+' — measured canopy height');ax.set_xlabel('m');ax.set_ylabel('m');evidence.append(dict(source=str(p.relative_to(ROOT.parent)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
fig.colorbar(im,ax=axes,label='Canopy height (m)');fig.suptitle('Sonoma development context: canopy patches, not identified individual trees');fig.savefig(ROOT/'results/geometry-context.png',dpi=120)
r=dict(status='analytic_patch_templates_not_individual_tree_reconstruction',geometry_evidence=evidence,development_test_windows_disjoint=True,assigned_dimensions=dict(total_height_m=[10,16],crown_base_m=[3,5],crown_diameter_m=[4,6],facade_m=[8,.5,6]),notes=['No orthophoto species or individual-crown identification performed; retain canopy-patch labels.','Facade solid obstruction 0.5 m thick; thermal wood layer is separately 0.02 m.','Reference generic fuel: 14 percent water per dry mass; density does not prove mature tree fuel loading.','Nominal source 4 MW per 4 m2 patch for 20 s with ramps; 78 MJ each.','Single receiver is3 m from crown edge; double adds16 m patch at (8,18).','Incoming radiation is FDS INCIDENT HEAT FLUX; convection stored separately. Compare positive excess radiation above initial ambient plus positive convection.','48 fixed west-face point probes, not spatially averaged1 m patches; raw full boundary outputs also retained.'])
(ROOT/'results/geometry-report.json').write_text(json.dumps(r,indent=2));print('Geometry report saved')
