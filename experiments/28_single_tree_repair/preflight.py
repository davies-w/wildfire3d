"""Check native startup, frozen vegetation, field headers and checkpoint resume."""
import json,os,subprocess,hashlib,csv,math
from pathlib import Path
import numpy as np
from scipy.io import FortranFile
from scipy.spatial import cKDTree
from build import ROOT,CLASSES,deck
BINARY=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def first_particles(path):
 f=FortranFile(path);f.read_ints();f.read_ints();labels=[]
 for _ in range(int(f.read_ints()[0])):
  qs=[]
  for _ in range(int(f.read_ints()[0])):qs.append(f.read_record('u1').tobytes().decode().strip());f.read_record('u1')
  labels.append(qs)
 while True:
  t=f.read_reals('f4')[0];parts=[]
  for qs in labels:
   n=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,n).T;tags=f.read_ints();q=f.read_reals('f4').reshape(len(qs),n).T if qs else None;parts.append((xyz,q,qs))
  if len(parts[0][0]):return parts

def main():
 rows=[];ts=json.loads((ROOT/'data/tree-templates.json').read_text())
 for c in json.loads((ROOT/'cases.json').read_text()):
  if c['split'] not in ['test']:continue
  folder=ROOT/'data/preflight'/c['case'];folder.mkdir(parents=True,exist_ok=True)
  source,expected=deck(c,ts);assert hashlib.sha256(source.encode()).hexdigest()==c['deck_sha256']
  short=source.replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01').replace('DT_PART=2.','DT_PART=.05')
  for stage,text in [('initial',short),('resume',short.replace('T_END=.1','T_END=.15').replace('&MISC RND_SEED=4321,','&MISC RESTART=T, RND_SEED=4321,'))]:
   (folder/'check.fds').write_text(text)
   with (folder/(stage+'.log')).open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=240)
   assert p.returncode==0 and 'completed successfully' in (folder/(stage+'.log')).read_text().lower(),str(folder)
   if stage=='initial':
    parts=first_particles(folder/(c['case']+'_1.prt5'))
    for fuel,(xyz,q,labels) in zip(CLASSES,parts[:4]):
     ex=[p for p in expected if p['fuel']==fuel];dist,idx=cKDTree(xyz).query([p['xyz'] for p in ex]);assert len(xyz)==400 and len(set(idx))==400 and max(dist)<5e-6
     assert labels[2]=='PARTICLE WEIGHTING FACTOR';assert np.max(abs(q[idx,2]/np.array([p['weight'] for p in ex])-1))<2e-6
    heater=parts[4][0];a=np.deg2rad(c['angle_deg']-30+60*(np.arange(1600)+.5)/1600);target=np.stack([8+1.2*np.cos(a),8+1.2*np.sin(a),np.full(1600,2.1)],axis=1)
    dist,idx=cKDTree(heater).query(target);assert len(heater)==1600 and len(set(idx))==1600 and max(dist)<5e-6
  assert list(folder.glob('*.restart'))
  with (folder/(c['case']+'_devc.csv')).open() as f:data=list(csv.reader(f));assert float(data[-1][0])>=.15-1e-6
  smv=(folder/(c['case']+'.smv')).read_text();assert 'INTEGRATED INTENSITY' in smv
  rows.append(dict(case=c['case'],passed=True,resumed=True,frozen_vegetation_verified=True,localized_heater_verified=True));(ROOT/'results/preflight.json').write_text(json.dumps(rows,indent=2));print('PASS',c['case'],flush=True)
if __name__=='__main__':
 main()
 (ROOT/'results/native-preflight.json').write_text(json.dumps(dict(passed=True,cases=json.loads((ROOT/'results/preflight.json').read_text()))))
