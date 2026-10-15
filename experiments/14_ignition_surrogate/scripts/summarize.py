"""Measured acceleration/error tables, source profiles, geometry QA and next-run manifest."""
import json
import csv
from pathlib import Path
import numpy as np
from benchmark import ROOT,REPO,write_json

def comparisons(file,key):
    rows=json.loads(file.read_text()); refs={r[key]:r for r in rows if r['variant']=='reference'}
    early={r[key]:r for r in rows if r['variant']=='early'}
    out=[]
    for v in sorted({r['variant'] for r in rows}-{'reference'}):
        pairs=[(refs[r[key]],r) for r in rows if r['variant']==v and r[key] in refs]
        good=[(a,b) for a,b in pairs if a['status']==b['status']=='complete']
        timing=[abs(a['ignition_time_s']-b['ignition_time_s']) for a,b in good if a['ignited'] and b['ignited']]
        out.append({'variant':v,'pairs':len(good),'missed_ignitions':sum(a['ignited'] and not b['ignited'] for a,b in good),
                    'false_ignitions':sum(not a['ignited'] and b['ignited'] for a,b in good),
                    'total_wall_speedup':sum(a['wall_seconds'] for a,b in good)/sum(b['wall_seconds'] for a,b in good),
                    'max_ignition_time_error_s':max(timing) if timing else None,
                    'speedup_vs_early_stopping':sum(early[b[key]]['wall_seconds'] for a,b in good)/sum(b['wall_seconds'] for a,b in good),
                    'timing_pairs':len(timing)})
    return out

def main():
    for name,count in [('benchmark',24),('transport',32)]:
        items=json.loads((ROOT/'results'/(name+'.json')).read_text())
        assert len(items)==count and all(r['status']=='complete' and r.get('label_reader_version')==2 for r in items), 'Finalize all runs with current event parser before reporting'
    profiles={}
    for case in ['with_tree','without_tree']:
        path=REPO/'experiments/13_ladder_tree_pair/data'/case/(case+'_cpu.csv')
        with path.open() as f:r=next(csv.DictReader(f))
        total=float(r['Total T_USED (s)'])
        profiles[case]={'source':str(path.relative_to(REPO)),'total_s':total,
                        'percent_by_routine':{k:round(100*float(v)/total,3) for k,v in r.items() if k not in ['Rank','Total T_USED (s)']}}
    write_json(ROOT/'results'/'existing_profiles.json',profiles)
    report={'coupon':comparisons(ROOT/'results/benchmark.json','flux_kW_m2'),
            'caveat':'Single wall-time measurements, no statistical speedup confidence intervals; synthetic screening, not real-world validation.'}
    if (ROOT/'results/transport.json').exists():report['transport']=comparisons(ROOT/'results/transport.json','scenario')
    if (ROOT/'results/reference_repeat.json').exists():
        repeat=json.loads((ROOT/'results/reference_repeat.json').read_text())
        original=next(r for r in json.loads((ROOT/'results/transport.json').read_text()) if r['scenario']==1 and r['variant']=='reference')
        report['reference_repeat']={'classification_agrees':repeat['ignited']==original['ignited'],
            'ignition_time_difference_s':abs(repeat['ignition_time_s']-original['ignition_time_s']) if repeat['ignited'] and original['ignited'] else None,
            'original_wall_seconds':original['wall_seconds'],'repeat_wall_seconds':repeat['wall_seconds'],
            'wall_time_ratio':repeat['wall_seconds']/original['wall_seconds'],
            'note':'One repeat; no estimate of tail uncertainty or statistical equivalence'}
        report['caveat'] += ' Identical reference runtime changed substantially; wall-time ratios are confounded by uncontrolled machine load.'
    write_json(ROOT/'results'/'comparison.json',report)
    properties=json.loads((ROOT/'results/properties.json').read_text())
    manifest=[]
    for p in properties:
        for direction in [0,90,180,270]:
            for speed in [0,3,6,9,12]:
                manifest.append({'id':f"{p['id']}_d{direction}_v{speed}",'property_id':p['id'],
                    'wind_from_degrees':direction,'wind_speed_m_s':speed,'exposure_duration_s':600,
                    'moisture':None,'ignition_origins':None,'probability_weight':None,
                    'status':'not_runnable_requires_geometry_material_fuel_and_exposure_review',
                    'sampling':'exploratory coverage grid, not a calibrated weather distribution'})
    write_json(ROOT/'scenario_manifest.json',manifest)
    lines=['# Measured pilot findings','',
           '57 synthetic FDS runs: 24 heated-wall checks, 32 coupled flame/radiation runs, and one reference repeat. These are not simulations of the 12 acquired properties.','',
           '## Coupled flame/radiation screening','',
           '| Configuration | Speedup vs full reference | Extra speedup vs early stopping | Missed / false ignitions | Maximum time difference |',
           '|---|---:|---:|---:|---:|']
    for r in report['transport']:
        lines.append(f"| {r['variant']} | {r['total_wall_speedup']:.2f}× | {r['speedup_vs_early_stopping']:.2f}× | {r['missed_ignitions']} / {r['false_ignitions']} | {r['max_ignition_time_error_s']:.3f} s |")
    lines += ['', 'Eight scenarios, four of which ignite in the reference; a 30 s exposure horizon. Aggregate speedup is the sum of reference wall times divided by the sum of variant wall times. Single timing samples include startup; no confidence interval is established.', '',
              'Time differences apply only when both runs ignite; classification differences must be considered separately. Radiation and coarse variants include early stopping. The coarse case changes both spatial and temporal discretization.', '',
              f"Reference repeat ignition-time difference: {report['reference_repeat']['ignition_time_difference_s']:.5f} s. Runtime changed from {report['reference_repeat']['original_wall_seconds']:.2f} to {report['reference_repeat']['repeat_wall_seconds']:.2f} s ({report['reference_repeat']['wall_time_ratio']:.2f}×). Other applications were observed consuming substantial CPU at the end of the experiment. The speed ratios above are preliminary, not controlled performance estimates. One repeat cannot quantify all variability.", '',
              '## Acquired properties','',
              '12 registered 120 × 120 m observation meshes and scene arrays, sourced from public Sonoma data. County records: 11 single-family and 1 multifamily residence. DEM/canopy feet-to-metres conversion is explicit. Individual species, materials, fences and eaves remain unverified. These scenes are not yet eligible for training.', '',
              '## Consequences','',
              '- Early stopping is the first practical acceleration candidate; qualify it on full property scenarios before adopting it.',
              '- Coarsening trades substantial ignition-time accuracy for speed. This screen does not establish an acceptable error bound.',
              '- Radiation tuning saves additional work but changes ignition timing; retain a separate acceptance test.',
              '- Existing experiment 13 profiles put radiation at about 21%, output at about 6%, particles at about 0.5%. Particle thinning is not a promising first optimization on those cases.',
              '- The 240-entry property scenario manifest is a preparation artifact, not 240 executed or accepted training labels.', '',
              'See comparison.json, transport.json, benchmark.json, reference_repeat.json, existing_profiles.json and boundary_check.json for machine-readable measurements; see ../README.md for reproduction and limitations.']
    (ROOT/'results/findings.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
