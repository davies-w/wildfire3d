"""Read existing outputs only: particle mass, HRR, devices and raw wall BNDF."""
import csv,json,math,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
CASES=[('cloud','validation_07_AC_s1234'),('cloud','validation_09_AD_s1234'),
       ('cloud','validation_11_AD_s1234'),('reused/cloud','calibration_03'),
       ('reused/cloud','calibration_02'),('reused/cloud','train_A_1p5')]+[('cloud',f'train_{i:02d}_{layout}_s1234') for i,layout in enumerate(['A','B','C','D','CD'],1)]
WINDOWS=[(0,10),(10,20),(20,30),(32,60)]
def read(path):
    with path.open() as f:
        rows=csv.reader(f);next(rows);keys=[v.strip().strip('"') for v in next(rows)]
        values=np.array([list(map(float,row)) for row in rows if row])
    return {k:values[:,i] for i,k in enumerate(keys)}
def main():
    out=ROOT/'data/diagnosis-boundary';out.mkdir(exist_ok=True)
    binary=ROOT.parents[1]/'FDS/install/bin/fds2ascii'
    results=[]
    for origin,name in CASES:
        folder=ROOT/'data'/origin/name;r=json.loads((folder/'result.json').read_text())
        d=read(folder/(name+'_devc.csv'));h=read(folder/(name+'_hrr.csv'));t=d['Time']
        hit=t[d['house_burn_max']>1e-9];first=float(hit[0]) if len(hit) else None
        mass=sum(d[k] for k in d if k.startswith('mass '));m1=float(np.interp(1,t,mass))
        entry=dict(case=name,layout=r['layout'],total_source_kw=r['total_source_kw'],ignition_s=first,
            peak_wall_C=float(max(d['house_max'])),peak_wall_time_s=float(t[np.argmax(d['house_max'])]),
            particle_mass_kg={str(s):float(np.interp(s,t,mass)) for s in (1,10,30,60,90)},
            total_HRR_kw={str(s):float(np.interp(s,h['Time'],h['HRR'])) for s in (10,30,40,60,90)},
            particle_mass_loss_1_to_10_kg=m1-float(np.interp(10,t,mass)),
            west_wall_temperature_C={str(s):float(np.interp(s,t,d['west_temp'])) for s in (10,15,20,30,40,60)},
            boundary=[])
        for start,end in WINDOWS:
            for quantity,index in [('WALL TEMPERATURE',1),('GAUGE HEAT FLUX',2)]:
                target=out/f'{name}_{index}_{start}_{end}.csv'
                if not target.exists():
                    answers=f'{name}\n3\n1\nn\n{start} {end}\n-1\n1\n{index}\n{target}\n'
                    p=subprocess.run([str(binary)],cwd=folder,input=answers,text=True,capture_output=True,check=True,timeout=60)
                    target.with_suffix('.log').write_text(p.stdout+p.stderr)
                values=[]
                for line in target.read_text().splitlines():
                    try:v=list(map(float,line.split(',')))
                    except ValueError:continue
                    if len(v)==4 and math.isfinite(v[3]) and abs(v[0]-14)<1e-4 and 9.9999<=v[1]<=14.0001 and -.0001<=v[2]<=4.0001:values.append(v)
                assert values,(name,quantity,start,end)
                strongest=max(values,key=lambda v:v[3])
                entry['boundary'].append(dict(quantity=quantity,window_s=[start,end],
                    max_patch_window_mean=strongest[3],patch_xyz=strongest[:3],
                    mean_of_samples=float(np.mean([v[3] for v in values])),samples=len(values),
                    entirely_before_house_ignition=first is None or end<first))
        results.append(entry)
    report=dict(cases=results,
        boundary_surface='Upwind west structure face x=14, y=10..14, z=0..4; core mesh 1, IOR=-1',
        caveats=['Particle mass loss includes drying, pyrolysis and oxidation; it is not a direct combustion-energy measure.',
        'Total HRR includes ignition burners, vegetation, gas burning and, after ignition, the structure.',
        'Boundary values are per-patch time averages. Gauge heat flux is an exposure diagnostic, not absorbed wall heat flux.',
        'No velocity slices or separately resolved convective/radiative wall-flux histories were saved. Plume deflection and shielding mechanisms cannot be uniquely identified.',
        'Burner-only controls were not run, so vegetation versus direct burner contribution to house ignition is unresolved.'])
    (ROOT/'results/diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in results:
        b=[x for x in r['boundary'] if x['quantity']=='GAUGE HEAT FLUX']
        print(r['case'],'wall peak',round(r['peak_wall_C'],1),'HRR40',round(r['total_HRR_kw']['40'],1),
              'west max patch mean flux',[round(x['max_patch_window_mean'],2) for x in b])
if __name__=='__main__':main()
