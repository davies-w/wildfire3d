"""Native setup audit; excludes all held-out FDS outputs."""
import csv,json,os,subprocess,hashlib
from pathlib import Path
import numpy as np
from scipy.io import FortranFile
from scipy.spatial import cKDTree
from build import ROOT,CLASSES,MODELS,deck
import math,copy
BINARY=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def read_particles(path):
 f=FortranFile(path);f.read_ints();f.read_ints();nc=int(f.read_ints()[0]);labels=[]
 for i in range(nc):
  n=int(f.read_ints()[0]);qs=[]
  for _ in range(n):qs.append(f.read_record('u1').tobytes().decode().strip());f.read_record('u1')
  labels.append(qs)
 while True:
  time=float(f.read_reals('f4')[0]);ps=[]
  for qs in labels:
   count=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,count).T;tags=f.read_ints();q=f.read_reals('f4').reshape(len(qs),count).T if qs else None;ps.append((xyz,q,qs))
  if ps[0][0].shape[0]:return time,ps

def main():
 ts=json.loads((ROOT/'data/tree-templates.json').read_text());cases=json.loads((ROOT/'cases.json').read_text());rows=[]
 # Every distinct type, translation and heater-only arrangement in DEVELOPMENT.
 selected=[c for c in cases if c['split']=='train' and (c['family']!='single' or c['case'].endswith('_1'))]
 shift=copy.deepcopy(next(c for c in selected if c['case']=='t26_single_C_1'));shift.update(case='t26_audit_C_translation',audit=True);shift['trees'][0].update(x=11.237,y=8.419);shift['heater_xy']=[11.237,8.419]
 expanded=copy.deepcopy(selected[0]);expanded.update(case='t26_audit_A_domain',audit=True,expanded=True)
 selected.extend([shift,expanded])
 for c in selected:
  folder=ROOT/'data/preflight'/c['case'];folder.mkdir(exist_ok=True)
  text,expected=deck(c,ts)
  if not c.get('audit'):assert hashlib.sha256(text.encode()).hexdigest()==c['deck_sha256']
  if c.get('expanded'):text=text.replace('IJK=40,40,30, XB=0,20,0,20,0,15','IJK=64,64,48, XB=-6,26,-6,26,0,24')
  short=text.replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01').replace('DT_PART=2.','DT_PART=.05')
  env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0')
  for tag,s in [('initial',short),('resume',short.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'))]:
   (folder/'check.fds').write_text(s)
   with (folder/(tag+'.log')).open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
   assert p.returncode==0 and 'completed successfully' in (folder/(tag+'.log')).read_text().lower(),(c['case'],(folder/(tag+'.log')).read_text()[-2500:])
   if tag=='initial':
    t,parts=read_particles(folder/(c['case']+'_1.prt5'));checks=[]
    for fuel,(xyz,q,labels) in zip(CLASSES,parts[:4]):
     exp=[p for p in expected if p['fuel']==fuel];target=np.array([p['xyz'] for p in exp]);dist,idx=cKDTree(xyz).query(target);assert len(xyz)==len(exp) and len(set(idx))==len(idx) and dist.max()<5e-6
     assert labels[2]=='PARTICLE WEIGHTING FACTOR',labels
     weights=np.array([p['weight'] for p in exp]);err=np.max(abs(q[idx,2]/weights-1));assert err<2e-6
     checks.append(dict(fuel=fuel,count=len(xyz),max_coordinate_error_m=float(dist.max()),max_weight_relative_error=float(err),wet_mass_kg=float(np.sum(q[:,1]*q[:,2]))))
    heater=parts[4][0];exp=np.array([np.array(p['xyz'])+np.array([*c['heater_xy'],0]) for p in ts[c['heater_type']]['heater']]);dist,idx=cKDTree(heater).query(exp);assert len(heater)==1600 and dist.max()<5e-6 and len(set(idx))==1600
  with (folder/(c['case']+'_devc.csv')).open() as f:data=list(csv.reader(f));assert float(data[-1][0])>=.15-1e-6
  assert list(folder.glob('*.restart'))
  for k,check in enumerate(checks):
   density=[1.683,.289,.263,.394][k];expected_mass=sum(math.pi*MODELS[n['type']]['r']**2*MODELS[n['type']]['height']/(3 if MODELS[n['type']]['shape']=='cone' else 1)*density*1.12 for n in c['trees'])
   assert abs(check['wet_mass_kg']/expected_mass-1)<.001,(check,expected_mass)
   check['expected_wet_mass_kg']=expected_mass
  rows.append(dict(case=c['case'],passed=True,first_particle_time_s=t,vegetation=checks,heater_coordinate_error_m=float(dist.max()),resumed=True))
  (ROOT/'results/preflight.json').write_text(json.dumps(rows,indent=2));print('PASS',c['case'],flush=True)
if __name__=='__main__':main()
