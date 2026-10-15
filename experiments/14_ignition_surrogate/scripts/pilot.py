"""Acquire public Sonoma geometry; retain uncertainty instead of invented labels.

Run from the experiment directory with the repository virtualenv.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import requests
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from pyproj import Transformer
from shapely.geometry import Polygon, mapping, box
from scipy import ndimage

ITEMS = {'dem': '8d47c0e1709c4acc9a34bc788b20252e',
         'dsm': 'e5111ae4fd584ddfade4d4cf53294cb2',
         'canopy': 'c1a8c024f48d4ae4bbf9ce1e76f5c84e'}
BUILDINGS = 'https://socogis.sonomacounty.ca.gov/map/rest/services/BASEPublic/Buildings/FeatureServer/0'
ROOT = Path(__file__).resolve().parents[1]

def get(url, **params):
    r = requests.get(url, params=params, timeout=90)
    r.raise_for_status()
    d = r.json()
    if 'error' in d:
        raise RuntimeError(d['error'])
    return d

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False))

def acquire():
    data = ROOT / 'data' / 'sonoma'
    data.mkdir(parents=True, exist_ok=True)
    services = {}
    for name, item in ITEMS.items():
        meta = get('https://www.arcgis.com/sharing/rest/content/items/' + item, f='json')
        save(data / (name + '_item.json'), meta)
        services[name] = meta['url']
        save(data / (name + '_service.json'), get(meta['url'], f='json'))
    save(data / 'buildings_metadata.json', get(BUILDINGS, f='json'))
    # Three predeclared geographic strata; selection is geometry-only, not risk-based.
    regions = [('santa_rosa_east', -122.649, 38.461),
               ('glen_ellen', -122.524, 38.365),
               ('sebastopol', -122.836, 38.403)]
    project = Transformer.from_crs(4326, 26910, always_xy=True)
    selected = []
    for region, lon, lat in regions:
        x, y = project.transform(lon, lat)
        bounds = [x-800, y-800, x+800, y+800]
        query = dict(f='json', where='1=1', geometry=','.join(map(str, bounds)),
                     geometryType='esriGeometryEnvelope', inSR=26910, outSR=26910,
                     spatialRel='esriSpatialRelIntersects', outFields='*',
                     returnGeometry='true', resultRecordCount=2000, orderByFields='OBJECTID')
        features = get(BUILDINGS + '/query', **query)
        while features.get('exceededTransferLimit'):
            page = get(BUILDINGS + '/query', **query, resultOffset=len(features['features']))
            if not page.get('features'):
                raise RuntimeError('Pagination made no progress')
            features['features'].extend(page['features'])
            features['exceededTransferLimit'] = page.get('exceededTransferLimit', False)
        save(data / (region + '_buildings.json'), features)
        candidates = []
        for f in features['features']:
            rings = f['geometry']['rings']
            # Reject multipart/holed candidates rather than guessing topology.
            if len(rings) != 1:
                continue
            p = Polygon(rings[0])
            if p.is_valid and 80 <= p.area <= 350:
                candidates.append((p, f))
        candidates.sort(key=lambda pf: pf[0].centroid.distance(Polygon.from_bounds(*bounds).centroid))
        chosen = []
        for p, f in candidates:
            if all(p.centroid.distance(other.centroid) > 140 for other, _ in chosen):
                chosen.append((p, f))
            if len(chosen) == 4:
                break
        for p, f in chosen:
            pid = f'{region}_{len(selected):02d}'
            folder = data / pid
            folder.mkdir(exist_ok=True)
            cx, cy = p.centroid.x, p.centroid.y
            extent = [cx-60, cy-60, cx+60, cy+60]
            save(folder / 'footprint.json', {'geometry': mapping(p), 'attributes': f['attributes'],
                                            'crs': 'EPSG:26910'})
            for name, url in services.items():
                dest = folder / (name + '.tif')
                reusable=False
                if dest.exists():
                    with rasterio.open(dest) as existing:
                        reusable=existing.crs.to_epsg()==26910 and np.allclose(existing.bounds,extent,rtol=0,atol=0.001)
                if not reusable:
                    export = get(url + '/exportImage', f='json', bbox=','.join(map(str, extent)),
                                 bboxSR=26910, imageSR=26910, size='120,120', format='tiff',
                                 pixelType='F32', interpolation='RSP_NearestNeighbor',
                                 renderingRule=json.dumps({'rasterFunction': 'None'}))
                    save(folder / (name + '_export.json'), export)
                    r = requests.get(export['href'], timeout=90)
                    r.raise_for_status()
                    dest.write_bytes(r.content)
                with rasterio.open(dest) as src:
                    if src.count != 1 or src.crs.to_epsg() != 26910:
                        raise RuntimeError(f'Unexpected raster format {dest}')
            selected.append({'id': pid, 'region': region, 'extent_utm_m': extent,
                             'footprint_area_m2': p.area,
                             'county_recorded_use':f['attributes'].get('PropType'),
                             'use_status':'county record, not field verified'})
            print('acquired', pid, flush=True)
    save(data / 'selection.json', selected)
    save(data / 'provenance.json', {'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         'sources': services, 'buildings': BUILDINGS,
         'sha256': {str(p.relative_to(data)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in data.rglob('*.tif')},
         'notes': '2022 LiDAR derivatives; building vintages vary. Metadata retained verbatim. No species/material inference.'})

def reconstruct():
    data = ROOT / 'data' / 'sonoma'
    # Horizontal reprojection does NOT convert raster elevation values.
    # Service descriptions override contradictory generic portal-item text.
    scales = {'dem': 0.3048, 'dsm': 1.0, 'canopy': 0.3048}
    for name in ('dem','canopy'):
        metadata=json.loads((data/(name+'_service.json')).read_text())
        if 'converts pixel values from meters to feet' not in metadata['serviceDescription']:
            raise RuntimeError('Elevation units changed; review service metadata')
    summaries = []
    for entry in json.loads((data / 'selection.json').read_text()):
        folder = data / entry['id']
        derived = ROOT / 'data' / 'scenes' / entry['id']
        derived.mkdir(parents=True,exist_ok=True)
        arrays = {}
        for name in ITEMS:
            with rasterio.open(folder / (name+'.tif')) as src:
                arrays[name] = src.read(1, masked=True).filled(np.nan) * scales[name]
                if name == 'dem':
                    transform, crs, shape = src.transform, src.crs, src.shape
                elif src.transform != transform or src.shape != shape:
                    raise RuntimeError('Raster registration mismatch')
        geom = json.loads((folder/'footprint.json').read_text())['geometry']
        mask = geometry_mask([geom], out_shape=shape, transform=transform, invert=True)
        height = arrays['dsm'] - arrays['dem']
        valid = np.isfinite(height) & (height >= -1) & (height < 100)
        roof = height[mask & valid]
        if len(roof) < 20:
            raise RuntimeError('Insufficient valid roof observations')
        # 2.5D source geometry: does not resolve under-canopy air, eaves or fences.
        canopy = np.where(np.isfinite(arrays['canopy']), arrays['canopy'], 0)
        canopy_overlap=float((canopy[mask]>2).mean())
        unobscured=mask & valid & (canopy<1)
        visible_roof=height[unobscured & (height>2)]
        context=json.loads((data/(entry['region']+'_buildings.json')).read_text())
        context_geometries=[mapping(Polygon(f['geometry']['rings'][0])) for f in context['features']]
        building_mask=geometry_mask(context_geometries,out_shape=shape,transform=transform,invert=True)
        vegetation_mask = (canopy > 1) & ~building_mask & valid
        components, n = ndimage.label(vegetation_mask)
        vegetation = []
        for i in range(1, n+1):
            rows, cols = np.where(components == i)
            if len(rows) < 4:
                continue
            vegetation.append({'id': f'vegetation_{i}', 'pixel_count': len(rows),
                 'height_p90_m': float(np.percentile(canopy[rows,cols],90)),
                 'bbox_local_m': [int(cols.min()),int(cols.max()+1),int(shape[0]-rows.max()-1),int(shape[0]-rows.min())],
                 'species': None, 'fuel_properties': None,
                 'classification': 'connected elevated-canopy region; may contain multiple plants'})
        model = {'id': entry['id'], 'geometry_status':'unvalidated 2.5D reconstruction',
                 'crs': str(crs), 'transform': list(transform), 'source_year':2022,
                 'vertical_units':'meters', 'source_vertical_scale_to_m':scales,
                 'unit_note':'DEM/CHM service says feet; portal item text conflicts. International foot used; survey-foot difference negligible here.',
                 'main_structure': {'footprint':geom, 'observed_height_over_footprint_p10_m':float(np.percentile(roof,10)),
                    'observed_height_over_footprint_p90_m':float(np.percentile(roof,90)),
                    'canopy_overlap_fraction':canopy_overlap,
                    'roof_height_estimate_m':float(np.median(visible_roof)) if len(visible_roof)>=20 else None,
                    'roof_height_estimate_method':'median DSM minus DTM where canopy <1m and height >2m; unvalidated',
                    'roof_material':None,
                    'siding_material':None, 'residential_use_verified':False,
                    'county_recorded_use':entry.get('county_recorded_use')},
                 'vegetation':vegetation, 'missing':['fences','decks','eaves','vents','fuel moisture','fuel loading','species','assemblies'],
                 'eligible_for_training':False}
        save(derived/'scene.json',model)
        np.savez_compressed(derived/'geometry.npz', dem=arrays['dem'], dsm=arrays['dsm'],
                            canopy=arrays['canopy'], main_building=mask, valid=valid)
        # Export observed surface as a metric mesh, not a claimed watertight solid.
        z = arrays['dsm'] - float(np.nanmin(arrays['dem']))
        with (derived/'observed_surface.obj').open('w') as out:
            out.write('# LiDAR surface mesh; missing data faces omitted; no material/species claims\n')
            for row in range(shape[0]):
                for col in range(shape[1]):
                    out.write(f'v {col+0.5} {shape[0]-row-0.5} {z[row,col] if valid[row,col] else 0:.3f}\n')
            for row in range(shape[0]-1):
                for col in range(shape[1]-1):
                    if valid[row:row+2,col:col+2].all():
                        a=row*shape[1]+col+1; b=a+1; c=a+shape[1]; d=c+1
                        out.write(f'f {a} {c} {b}\nf {b} {c} {d}\n')
        summaries.append({**entry,'observed_height_over_footprint_p90_m':model['main_structure']['observed_height_over_footprint_p90_m'],
                          'canopy_overlap_fraction':canopy_overlap,
                          'roof_height_estimate_m':model['main_structure']['roof_height_estimate_m'],
                          'vegetation_regions':len(vegetation),'valid_fraction':float(valid.mean())})
    save(ROOT/'results'/'properties.json',summaries)
    print('reconstructed',len(summaries),'candidate scenes')

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['acquire','reconstruct']);args=ap.parse_args()
    {'acquire':acquire,'reconstruct':reconstruct}[args.action]()
