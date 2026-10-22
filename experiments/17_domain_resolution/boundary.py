"""Verify the complete structure's six faces from raw BNDF via fds2ascii."""
import json,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;binary=ROOT.parents[1]/'FDS/install/bin/fds2ascii'
summary=json.loads((ROOT/'data/cloud/campaign.json').read_text());outdir=ROOT/'data/boundary';outdir.mkdir(parents=True,exist_ok=True);records=[]
for r in summary['results']:
    if not r['full_horizon']:continue
    name=r['case'];folder=ROOT/'data/cloud'/name
    # Temperature near the detected crossing, or peak time if no crossing.
    import csv
    with (folder/(name+'_devc.csv')).open() as f:
        it=csv.reader(f);next(it);keys=[x.strip().strip('"') for x in next(it)];rows=[dict(zip(keys,map(float,row))) for row in it if row]
    peak=max(rows,key=lambda x:x['house_max'])['Time'];event=r.get('first_ignition_s') or peak
    # Include at least two BNDF frames and one after the event. Burning checked over full horizon.
    windows={1:(max(0,2*math.floor(event/2)-2),min(90,2*math.ceil(event/2)+4)),3:(0,90)}
    for quantity,index in [('WALL TEMPERATURE',1),('BURNING RATE',3)]:
        start,end=windows[index];values=[]
        for face in [-1,1,-2,2,-3,3]:
            target=outdir/f'{name}_{index}_{face}.csv'
            if not target.exists():
                answers=f'{name}\n3\n1\nn\n{start} {end}\n{face}\n1\n{index}\n{target}\n'
                p=subprocess.run([str(binary)],cwd=folder,input=answers,capture_output=True,text=True,timeout=60,check=True)
                (target.with_suffix('.log')).write_text(p.stdout+p.stderr)
            for line in target.read_text().splitlines():
                try:
                    row=list(map(float,line.split(',')))
                    if len(row)==4 and math.isfinite(row[3]) and 14-1e-4<=row[0]<=20+1e-4 and 10-1e-4<=row[1]<=14+1e-4 and -1e-4<=row[2]<=4+1e-4:values.append(row[3])
                except ValueError:pass
        if not values:raise RuntimeError('No boundary values: '+name)
        records.append(dict(case=name,quantity=quantity,averaging_window_s=[start,end],maximum_time_averaged_value=max(values),minimum_time_averaged_value=min(values),positive_samples=sum(v>1e-12 for v in values),samples=len(values)))
result=dict(surface='All six structure faces x=14..20,y=10..14,z=0..4, core mesh 1',note='fds2ascii values are window averages, not instantaneous maxima. A below-350 average does not disprove a transient threshold crossing.',records=records)
(ROOT/'results/boundary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
