"""Full-horizon mechanism profiling; not a real-property ignition model."""
import argparse, csv, hashlib, json, os, platform, re, signal, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def generate():
    import shutil
    (ROOT/'decks').mkdir(exist_ok=True)
    for p in (ROOT/'inputs').glob('*.fds'):shutil.copyfile(p,ROOT/'decks'/p.name)
    cases=[]
    for mode in ['flow','fire']:
        for variant in ['coarse','medium','fine','split_fine','local_fine','radiation']:
            name=f'{mode}_{variant}'
            dx={'coarse':.5,'medium':.25,'radiation':.25}.get(variant,.125)
            blocks=[(0,8,dx)] if variant not in ['split_fine','local_fine'] else [(0,2,.25 if variant=='local_fine' else dx),(2,6,dx),(6,8,.25 if variant=='local_fine' else dx)]
            meshes='\n'.join(f"&MESH IJK={round((b-a)/d)},{round(4/d)},{round(4/d)}, XB={a},{b},0,4,0,4 /" for a,b,d in blocks)
            cells=sum(round((b-a)/d)*round(4/d)**2 for a,b,d in blocks)
            radiation="&RADI NUMBER_RADIATION_ANGLES=50, TIME_STEP_INCREMENT=6 /" if variant=='radiation' else ''
            text=f"""&HEAD CHID='{name}', TITLE='Wind obstacle and surface heating resolution study' /
{meshes}
&TIME T_END=8. /
&MISC RND_SEED=1234 /
&WIND SPEED=3., DIRECTION=270. /
&REAC FUEL='PROPANE', SOOT_YIELD=0.01 /
&MATL ID='wood thermal surrogate', DENSITY=500., CONDUCTIVITY=0.12, SPECIFIC_HEAT=1.7 /
&SURF ID='TARGET', MATL_ID='wood thermal surrogate', THICKNESS=0.02 /
&SURF ID='BURNER', HRRPUA={1600 if mode=='fire' else 0}, TAU_Q=0. /
&OBST XB=4,4.5,1,3,0,2.5, SURF_ID='TARGET' /
&OBST XB=2.5,3.5,1.5,2.5,0,0.5, SURF_IDS='BURNER','INERT','INERT' /
&VENT MB='XMIN', SURF_ID='OPEN' /
&VENT MB='XMAX', SURF_ID='OPEN' /
&VENT MB='YMIN', SURF_ID='OPEN' /
&VENT MB='YMAX', SURF_ID='OPEN' /
&VENT MB='ZMAX', SURF_ID='OPEN' /
{radiation}
&DEVC ID='surface_max_C', QUANTITY='WALL TEMPERATURE', SURF_ID='TARGET', XB=0,8,0,4,0,4, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /
&DEVC ID='heat_max_kW_m2', QUANTITY='GAUGE HEAT FLUX', SURF_ID='TARGET', XB=0,8,0,4,0,4, SPATIAL_STATISTIC='MAX', TEMPORAL_STATISTIC='INSTANT VALUE' /
&DEVC ID='wake_u', XYZ=5.5,2,1, QUANTITY='U-VELOCITY' /
&DEVC ID='plume_C', XYZ=3.5,2,2, QUANTITY='TEMPERATURE' /
&BNDF QUANTITY='WALL TEMPERATURE' /
&BNDF QUANTITY='GAUGE HEAT FLUX' /
&DUMP DT_DEVC=0.1, DT_BNDF=1., DT_HRR=0.1, DT_RESTART=100000., SMOKE3D=.FALSE. /
&TAIL /
"""
            p=ROOT/'decks'/f'{name}.fds';p.parent.mkdir(exist_ok=True);p.write_text(text)
            cases.append(dict(case=name,mode=mode,variant=variant,cells=cells,meshes=len(blocks),horizon_s=8))
    for name in ['heat_conduction_a','pine_needles']:
        cases.append(dict(case=name,mode='upstream_verification',variant='original',cells=27 if name=='heat_conduction_a' else 1000,meshes=1,horizon_s=2000 if name=='heat_conduction_a' else 10))
    save(ROOT/'manifest.json',cases)

def read_csv(path):
    with path.open() as f:
        r=csv.reader(f);next(r);names=[s.strip().strip('"') for s in next(r)]
        return [dict(zip(names,map(float,row))) for row in r if row]

def analyze(folder,name,horizon):
    out=(folder/f'{name}.out').read_text(errors='replace') if (folder/f'{name}.out').exists() else ''
    steps=re.findall(r'Time Step\s+(\d+)',out)
    dts=re.findall(r'Step Size:\s+([\d.Ee+-]+)',out)
    cpu=folder/f'{name}_cpu.csv'
    profile={}
    if cpu.exists():
        with cpu.open() as f:
            rows=list(csv.DictReader(f))
        profile={k.strip():sum(float(r[k]) for r in rows) for k in rows[0] if k!='Rank'}
    dev=folder/f'{name}_devc.csv'
    rows=read_csv(dev) if dev.exists() else []
    complete=bool(rows) and rows[-1]['Time']>=horizon-1e-5 and 'completed successfully' in out.lower()
    return dict(full_horizon=complete,steps=int(steps[-1]) if steps else None,logged_dt_min_s=min(map(float,dts)) if dts else None,
                cpu_profile=profile,final_devices=rows[-1] if rows else {},output_bytes=sum(p.stat().st_size for p in folder.glob('*') if p.is_file()))

def run_one(case,repeat,label,binary,timeout=600):
    name=case['case']; folder=ROOT/'data'/label/f'{name}_r{repeat}'
    folder.mkdir(parents=True,exist_ok=True)
    deck=ROOT/'decks'/f'{name}.fds'
    result=dict(case,repeat=repeat,platform=platform.platform(),machine=platform.machine(),binary_sha256=sha(binary),deck_sha256=sha(deck),threads=4)
    result['load_before']=list(os.getloadavg())
    start=time.monotonic()
    with (folder/'run.log').open('w') as log:
        p=subprocess.Popen([str(binary),str(deck)],cwd=folder,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,OMP_NUM_THREADS='4',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1'))
        try: rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.wait();rc=124
    result.update(wall_seconds=time.monotonic()-start,returncode=rc,load_after=list(os.getloadavg()))
    result.update(analyze(folder,name,case['horizon_s']))
    save(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ['case','repeat','wall_seconds','returncode','full_horizon']}),flush=True)
    if rc or not result['full_horizon']:raise RuntimeError(f'Failed {name}; see {folder}')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','run']);ap.add_argument('--label',default='local');ap.add_argument('--cases',default='all');ap.add_argument('--repeat',type=int,default=1);args=ap.parse_args()
    if args.action=='generate':generate();return
    binary=Path(os.environ.get('FDS_BINARY',str(ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx')))
    cases=json.loads((ROOT/'manifest.json').read_text())
    if args.cases!='all':cases=[c for c in cases if c['case'] in args.cases.split(',')]
    if not cases:raise ValueError('No cases selected')
    for c in cases:run_one(c,args.repeat,args.label,binary)

if __name__=='__main__':main()
