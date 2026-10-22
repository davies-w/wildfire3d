"""Extract development data only by default. Test extraction requires frozen predictions."""
import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
import numpy as np
from models import ROOT,FACES,TIMES

def extract(split):
    if split=='test':
        assert (ROOT/'results/frozen-predictions.json').exists(),'Freeze predictions before reading test evidence'
    selected=json.loads((ROOT/('confirmation-inputs.json' if split=='test' else 'development-manifest.json')).read_text())
    boundary_dir=ROOT/'data/boundary'/split;boundary_dir.mkdir(parents=True,exist_ok=True)
    binary=ROOT.parents[1]/'FDS/install/bin/fds2ascii'
    records=[]
    for row in selected:
        name=row['case'];folder=ROOT/row['folder']
        r=json.loads((folder/'result.json').read_text())
        assert r['full_horizon'] and r['returncode']==0,'Incomplete case '+name
        with (folder/f'{name}_devc.csv').open() as f:
            it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)]
            values=np.array([list(map(float,v)) for v in it if v])
        assert np.isfinite(values).all()
        devices={k:values[:,i] for i,k in enumerate(keys)};t=devices['Time']
        hits=np.flatnonzero(devices['house_burn_max']>1e-9)
        ignition_time=float(t[hits[0]]) if len(hits) else None
        boundary={}
        for q,index in [('temperature',1),('burning_rate',3)]:
            found=[]
            for face in (-1,1,-2,2,-3,3):
                out=boundary_dir/f'{name}_{index}_{face}.csv'
                if not out.exists():
                    answer=f'{name}\n3\n1\nn\n0 90\n{face}\n1\n{index}\n{out}\n'
                    result=subprocess.run([str(binary)],cwd=folder,input=answer,text=True,capture_output=True,timeout=60,check=True)
                    out.with_suffix('.log').write_text(result.stdout+result.stderr)
                for line in out.read_text().splitlines():
                    try:v=list(map(float,line.split(',')))
                    except ValueError:continue
                    if len(v)==4 and math.isfinite(v[3]) and 13.9999<=v[0]<=20.0001 and 9.9999<=v[1]<=14.0001 and -.0001<=v[2]<=4.0001:found.append(v[3])
            assert found,'No boundary values '+name
            boundary[q]=dict(maximum_time_averaged_value=max(found),samples=len(found),averaging_window_s=[0,90])
        raw_label=boundary['burning_rate']['maximum_time_averaged_value']>1e-12
        assert raw_label==bool(len(hits)),'Boundary/device ignition mismatch '+name
        auxiliary=[]
        for face in FACES:
            temps=np.interp(TIMES,t,devices[face+'_temp'])/350
            flux=np.interp(TIMES,t,devices[face+'_flux'])
            flux=np.sign(flux)*np.log1p(abs(flux))/np.log(101)
            auxiliary.append(np.concatenate([temps,flux]).tolist())
        records.append(dict(case=name,split=row.get('split',split),layout=row['layout'],total_source_kw=r['total_source_kw'],duration_s=r.get('duration_s',30),seed=r.get('seed',1234),
            target=[int(raw_label),(ignition_time or 90)/90],first_ignition_s=ignition_time,
            auxiliary=auxiliary,boundary=boundary,deck_sha256=r['deck_sha256'],
            cpu_s=r['cpu_user_s']+r['cpu_system_s'],wall_s=r['wall_seconds'],
            device_sha256=hashlib.sha256((folder/f'{name}_devc.csv').read_bytes()).hexdigest()))
    (ROOT/f'data/{split}.json').write_text(json.dumps(records,indent=2)+'\n')
    print(f'Extracted {len(records)} {split} cases; raw boundary ignition cross-checks passed.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('split',choices=['development','test']);extract(p.parse_args().split)
