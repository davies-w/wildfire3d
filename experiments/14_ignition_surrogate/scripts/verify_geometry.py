"""Verify coordinate registration, coverage and preservation of unknown labels."""
import json
from pathlib import Path
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'results/properties.json').read_text())
assert len(entries)==12
checks=[]
for entry in entries:
    p=ROOT/'data/scenes'/entry['id']
    a=np.load(p/'geometry.npz');m=json.loads((p/'scene.json').read_text())
    assert a['main_building'].sum()>20
    assert a['valid'].mean()>.95
    assert m['eligible_for_training'] is False
    assert m['main_structure']['roof_material'] is None
    assert m['main_structure']['siding_material'] is None
    for name in ['dem','dsm','canopy']:
        with rasterio.open(ROOT/'data/sonoma'/entry['id']/(name+'.tif')) as src:
            assert src.crs.to_epsg()==26910
            assert np.allclose(src.bounds,entry['extent_utm_m'],rtol=0,atol=.001)
    checks.append({'id':entry['id'],'passed':True,'valid_fraction':float(a['valid'].mean()),
                   'canopy_overlap_fraction':entry['canopy_overlap_fraction']})
(ROOT/'results/geometry_checks.json').write_text(json.dumps(checks,indent=2))
print('12 source/geometry consistency checks passed')
