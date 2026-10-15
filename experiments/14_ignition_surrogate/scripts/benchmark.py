"""Small ignition-label and acceleration benchmark. No failed run is a negative label."""
import argparse
import csv
import hashlib
import json
import os
import re
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO))
from paths import NATIVE_FDS

def write_json(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2))

def deck(name, flux, dx, early, lean, duration=30):
    # Deliberately tiny externally heated coupon: validates event machinery,
    # not wildfire transport, tree combustion, or real construction assemblies.
    n=round(2/dx)
    return f"""&HEAD CHID='{name}', TITLE='Ignition event verification coupon' /
&MESH IJK={n},{n},{n}, XB=0,2,0,2,0,2 /
&TIME T_END={duration} /
&MISC RND_SEED=1234 /
&REAC FUEL='PROPANE' /
&MATL ID='WOOD', DENSITY=500., CONDUCTIVITY=0.12, SPECIFIC_HEAT=1.7 /
&SURF ID='MAIN_WALL', MATL_ID='WOOD', THICKNESS=0.02,
 HRRPUA=100., IGNITION_TEMPERATURE=350., EXTERNAL_FLUX={flux} /
&OBST XB=1,1.5,0.5,1.5,0,1.5, SURF_ID='MAIN_WALL' /
&VENT MB='XMIN', SURF_ID='OPEN' /
&VENT MB='XMAX', SURF_ID='OPEN' /
&VENT MB='YMIN', SURF_ID='OPEN' /
&VENT MB='YMAX', SURF_ID='OPEN' /
&VENT MB='ZMAX', SURF_ID='OPEN' /
&DEVC ID='ignition_wall', QUANTITY='WALL TEMPERATURE', SURF_ID='MAIN_WALL',
 XB=0,2,0,2,0,2, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE', SETPOINT=350. /
&DEVC ID='burning_wall', QUANTITY='BURNING RATE', SURF_ID='MAIN_WALL',
 XB=0,2,0,2,0,2, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /
{("&CTRL ID='ignition_stop', FUNCTION_TYPE='KILL', INPUT_ID='ignition_wall' /" if early else '')}
&BNDF QUANTITY='WALL TEMPERATURE' /
&BNDF QUANTITY='BURNING RATE' /
&DUMP DT_DEVC=0.05, DT_BNDF=0.25, DT_HRR=0.1, DT_RESTART=100000.,
 SMOKE3D={'.FALSE.' if lean else '.TRUE.'}, DT_PART=100000. /
&TAIL /
"""

def csv_rows(path):
    with path.open() as f:
        r=csv.reader(f); next(r); names=[s.strip().strip('"') for s in next(r)]
        return [dict(zip(names,map(float,row))) for row in r if row]

def classify(rows, returncode, log, horizon, event_time=None):
    if returncode != 0 or 'completed successfully' not in log.lower() or not rows:
        return {'status':'failed','ignited':None,'ignition_time_s':None}
    if any(not math.isfinite(r['Time']) or not math.isfinite(r['ignition_wall']) for r in rows):
        return {'status':'invalid_output','ignited':None,'ignition_time_s':None}
    if event_time is not None:
        if not math.isfinite(event_time) or not 0 <= event_time <= horizon+1e-3:
            return {'status':'invalid_output','ignited':None,'ignition_time_s':None}
        return {'status':'complete','ignited':True,'ignition_time_s':event_time}
    events=[r for r in rows if r['ignition_wall']>=350]
    if not events and rows[-1]['Time'] < horizon-1e-5:
        return {'status':'censored','ignited':None,'ignition_time_s':None}
    return {'status':'complete','ignited':bool(events),'ignition_time_s':events[0]['Time'] if events else None}

def analyze(folder,name,text,rc):
    log=(folder/'run.log').read_text(errors='replace')
    device=folder/(name+'_devc.csv')
    if not device.exists():return {'status':'failed','ignited':None,'ignition_time_s':None}
    rows=csv_rows(device)
    if not rows:return {'status':'failed','ignited':None,'ignition_time_s':None}
    event_time=None
    event_file=folder/(name+'_devc_ctrl_log.csv')
    if event_file.exists():
        with event_file.open() as f:
            for event in csv.DictReader(f):
                if event['Type'].strip()=='DEVC' and event['ID'].strip()=='ignition_wall' and event['State'].strip()=='T':
                    event_time=float(event['Time (s)']);break
    horizon=float(re.search(r'T_END\s*=\s*([\d.]+)',text).group(1))
    result=classify(rows,rc,log,horizon,event_time)
    result.update(last_time_s=rows[-1]['Time'],max_temperature_C=max(r['ignition_wall'] for r in rows),
                  label_source='FDS device activation event log; periodic samples for completed negatives',label_reader_version=2)
    return result

def run(name, text, timeout=180, scope='externally heated coupon; workflow verification only'):
    folder=ROOT/'data'/'benchmark'/name
    folder.mkdir(parents=True,exist_ok=True)
    inp=ROOT/'decks'/(name+'.fds'); inp.parent.mkdir(exist_ok=True); inp.write_text(text)
    binary=Path(NATIVE_FDS)
    digest=hashlib.sha256(text.encode()).hexdigest()
    binary_digest=hashlib.sha256(binary.read_bytes()).hexdigest()
    old=folder/'result.json'
    if old.exists():
        d=json.loads(old.read_text())
        if d.get('deck_sha256')==digest and d.get('binary_sha256')==binary_digest and d.get('status')=='complete':
            d.update(analyze(folder,name,text,d['returncode']))
            d['scope']=scope
            write_json(old,d)
            return d
    t0=time.monotonic()
    with (folder/'run.log').open('w') as log:
        try:
            p=subprocess.run([str(binary),str(inp)],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4'),
                             stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
            rc=p.returncode
        except subprocess.TimeoutExpired:
            rc=None
    log=(folder/'run.log').read_text(errors='replace')
    result={'case':name,'wall_seconds':time.monotonic()-t0,'returncode':rc,
            'deck_sha256':digest,'binary_sha256':binary_digest,'threads':4,
            'status':'failed','ignited':None,'ignition_time_s':None,
            'scope':scope}
    result.update(analyze(folder,name,text,rc))
    write_json(old,result)
    print(json.dumps(result),flush=True)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');args=ap.parse_args()
    results=[]
    fluxes=[0,100] if args.smoke else [0,15,25,40,60,100]
    for flux in fluxes:
        for variant,dx,early,lean in [('reference',0.25,False,False),('early',0.25,True,False),
                                     ('lean',0.25,True,True),('coarse',0.5,True,True)]:
            name=f'q{flux}_{variant}'
            d=run(name,deck(name,flux,dx,early,lean))
            d.update(flux_kW_m2=flux,variant=variant,dx_m=dx)
            results.append(d)
            write_json(ROOT/'results'/'benchmark.json',results)
            if d['status']!='complete':
                raise SystemExit('Failed or incomplete run: inspect log before proceeding')

if __name__=='__main__': main()
