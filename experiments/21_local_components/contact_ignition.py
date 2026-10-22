"""Local controlled crown ignition; preserve material, canopy, wind and building."""
import csv,hashlib,json,os,subprocess,time,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def build(name,horizon=90,particles=1600,temperature=1500,duration=20,bare=False):
 s=(ROOT/'decks/a21_single_upstream.fds').read_text().replace("CHID='a21_single_upstream'",f"CHID='{name}'").replace('T_END=180',f'T_END={horizon}')
 s=re.sub(r"&VENT XB=7.5,9.5,11,13,0,0, SURF_ID='IGNITOR' /",'',s)
 if bare:s=re.sub(r'&INIT\b.*?/', '',s,flags=re.S)
 extra=f"""
! Controlled ignition source following the reference tree's hot-particle approach.
! Artificial ignition exposure, not ground-fire or ember modelling.
&PART ID='contact ignitor', SAMPLING_FACTOR=1, SURF_ID='contact burner', STATIC=T, AGE={duration+1}, QUANTITIES='PARTICLE TEMPERATURE' /
&SURF ID='contact burner', TMP_FRONT={temperature}., EMISSIVITY=1., HRRPUA=60., RAMP_T='contact', RAMP_Q='contact', RADIUS=.01, GEOMETRY='SPHERICAL' /
&RAMP ID='contact', T=0., F=0. /
&RAMP ID='contact', T=.1, F=1. /
&RAMP ID='contact', T={duration}., F=1. /
&RAMP ID='contact', T={duration+.1}, F=0. /
&INIT PART_ID='contact ignitor', XYZ=11,12,3.1, RADIUS=1.5, SHAPE='RING', N_PARTICLES={particles} /
"""
 # Count support is checked in startup; particle archive also proves expiry.
 s=s.replace('&TAIL /',extra+'\n&TAIL /');return s

def run(name,horizon=90,**kw):
 folder=ROOT/'data/contact'/name;folder.mkdir(parents=True,exist_ok=False);s=build(name,horizon,**kw);(folder/(name+'.fds')).write_text(s)
 binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx';start=time.time()
 with (folder/'run.log').open('w') as f:p=subprocess.run([str(binary),name+'.fds'],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=2400)
 report=dict(case=name,returncode=p.returncode,wall_seconds=time.time()-start,deck_sha256=hashlib.sha256(s.encode()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cloud_spend_usd=0,settings=kw)
 (folder/'result.json').write_text(json.dumps(report,indent=2));assert p.returncode==0 and 'completed successfully' in (folder/'run.log').read_text().lower(),(folder/'run.log').read_text()[-2500:]
 if horizon>21:
  report.update(assess(name));(folder/'result.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report),flush=True)
def read(name,suffix):
 with (ROOT/'data/contact'/name/(name+suffix)).open() as f:
  it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)];a=np.array([list(map(float,v)) for v in it if v]);return {k:a[:,i] for i,k in enumerate(keys)}
def ignitor_count(name):
 lines=(ROOT/'data/contact'/name/(name+'_1.prt5.bnd')).read_text().splitlines();i=0;counts=[]
 while i<len(lines):
  t,nclass,_=map(float,lines[i].split());i+=1
  for c in range(int(nclass)):
   nq,n=map(int,lines[i].split());i+=1+nq
   if c==4 and t>=22:counts.append(n)
 return max(counts) if counts else None
def assess(name):
 d=read(name,'_devc.csv');h=read(name,'_hrr.csv');t=np.arange(40,60.01,.1);q=np.interp(t,h['Time'],h['HRR']);fuel=sum(d[k] for k in d if k.startswith('fuel_release '));m=sum(d[k] for k in d if k.startswith('mass '));return dict(physical_seconds=float(h['Time'][-1]),hrr_min_40_50_kw=float(min(q[t<=50])),energy_40_60_MJ=float(np.trapezoid(q,t)/1000),fuel_release_diagnostic_valid=False, fuel_release_diagnostic_issue='Unfiltered wall contributions are included in each PART_ID surface integral; do not sum as vegetation fuel.', wet_particle_mass_loss_40_60_kg=float(np.interp(40,d['Time'],m)-np.interp(60,d['Time'],m)),house_burning=bool(np.any(d['house_burn_max']>1e-9)),peak_house_C=float(max(d['house_max'])),initial_wet_mass_kg=float(m[1]),final_wet_mass_kg=float(m[-1]),ignitor_count_after_22=ignitor_count(name))
if __name__=='__main__':
 import sys
 run(sys.argv[1],horizon=float(sys.argv[2]) if len(sys.argv)>2 else 90)
