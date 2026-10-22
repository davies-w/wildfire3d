"""Diagnose completed cases using raw west-wall boundaries and device histories."""
import argparse,csv,json,math,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
BINARY=ROOT.parents[1]/'FDS/install/bin/fds2ascii'
def read(path):
    with path.open() as f:
        rows=csv.reader(f);next(rows);keys=[v.strip().strip('"') for v in next(rows)]
        data=np.array([list(map(float,v)) for v in rows if v])
    return dict(zip(keys,data.T))
def analyze(name):
    base=ROOT/'batches'/name;spec=json.loads((base/'batch.json').read_text());out=base/'data/boundary';out.mkdir(exist_ok=True)
    records=[]
    for case in spec['cases']:
        name=case['case'];folder=base/'data/cloud'/name
        if not (folder/'result.json').exists():continue
        r=json.loads((folder/'result.json').read_text())
        if not r['full_horizon']:continue
        d=read(folder/(name+'_devc.csv'));h=read(folder/(name+'_hrr.csv'));t=d['Time']
        hits=t[d['house_burn_max']>1e-9];first=float(hits[0]) if len(hits) else None
        entry=dict(r,ignited=first is not None,first_ignition_s=first,peak_house_C=float(max(d['house_max'])),
                   total_HRR_kw={str(s):float(np.interp(s,h['Time'],h['HRR'])) for s in (10,20,30,40,60,90)},boundary=[])
        for index,quantity in enumerate(('WALL TEMPERATURE','GAUGE HEAT FLUX','BURNING RATE','RADIATIVE HEAT FLUX','CONVECTIVE HEAT FLUX','TOTAL HEAT FLUX'),1):
            windows=[(0,90)] if index==3 else [(0,10),(10,20),(20,30),(32,60)]
            for start,end in windows:
                target=out/f'{name}_{index}_{start}_{end}.csv'
                if not target.exists():
                    answers=f'{name}\n3\n1\nn\n{start} {end}\n-1\n1\n{index}\n{target}\n'
                    p=subprocess.run([str(BINARY)],cwd=folder,input=answers,text=True,capture_output=True,check=True,timeout=60)
                    target.with_suffix('.log').write_text(p.stdout+p.stderr)
                samples=[]
                for line in target.read_text().splitlines():
                    try:v=list(map(float,line.split(',')))
                    except ValueError:continue
                    if len(v)==4 and math.isfinite(v[3]) and abs(v[0]-14)<1e-4 and 9.9999<=v[1]<=14.0001 and -.0001<=v[2]<=4.0001:samples.append(v)
                assert samples,(name,index,start,end)
                best=max(samples,key=lambda v:v[3]);entry['boundary'].append(dict(quantity=quantity,window_s=[start,end],maximum_patch_mean=best[3],patch_xyz=best[:3],preignition=first is None or end<first))
        burning=[]
        for face in (-1,1,-2,2,-3,3):
            target=out/f'{name}_house_burn_{face}.csv'
            if not target.exists():
                answers=f'{name}\n3\n1\nn\n0 90\n{face}\n1\n3\n{target}\n'
                p=subprocess.run([str(BINARY)],cwd=folder,input=answers,text=True,capture_output=True,check=True,timeout=60)
                target.with_suffix('.log').write_text(p.stdout+p.stderr)
            for line in target.read_text().splitlines():
                try:v=list(map(float,line.split(',')))
                except ValueError:continue
                if len(v)==4 and math.isfinite(v[3]) and 13.9999<=v[0]<=20.0001 and 9.9999<=v[1]<=14.0001 and -.0001<=v[2]<=4.0001:burning.append(v[3])
        assert burning,'No house boundary burning samples'
        assert (max(burning)>1e-12)==entry['ignited'],'Boundary/device ignition mismatch'
        entry['all_house_boundary_burning_rate']=dict(maximum_patch_mean=max(burning),samples=len(burning),window_s=[0,90],device_label_agrees=True)
        records.append(entry)
    report=dict(cases=records,surface='West house wall x=14,y=10..14,z=0..4,mesh 1,IOR=-1',
        caveats=['Boundary fluxes are maxima of patch time averages, not instantaneous or whole-wall integrated values.',
        'Flux maxima may occur on different patches: do not add independently maximized radiative and convective fluxes.',
        'Post-ignition flux and HRR include house-fire feedback.',
        'Ignition labels are independently checked against all six house surface orientations in raw boundary output.'])
    (base/'results/diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(case=r['case'],ignited=r['ignited'],peak_house_C=r['peak_house_C']) for r in records],indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');analyze(p.parse_args().batch)
