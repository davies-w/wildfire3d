"""Short native input checks only: geometry, moisture mass, seeds. No training/cloud."""
from pathlib import Path
import json,os,subprocess,hashlib
import numpy as np
from scipy.spatial import cKDTree
from particle_reader import first
R=Path(__file__).parent;B=R.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
def main():
 cs=json.loads((R/'cases.json').read_text());templates=json.loads((R/'data/tree-templates.json').read_text());repeat=next(c for c in cs if c['replica']==1);base=next(c for c in cs if c['configuration']==repeat['configuration'] and c['replica']==0);chosen=[min(cs,key=lambda c:(c['moisture'],c['crown_height_m'])),max(cs,key=lambda c:(c['moisture'],c['crown_height_m'])),base,repeat];seen=set();rows=[]
 ref=first(R.parent/'27_single_tree_cnn/data/cloud/s27_train_0/s27_train_0_1.prt5');fuels=['foliage','small roundwood','medium roundwood','large roundwood'];dry=[float(q[0,1])/1.12 for x,q in ref[:4]]
 for c in chosen:
  if c['case'] in seen:continue
  seen.add(c['case']);f=R/'data/preflight'/c['case'];f.mkdir(parents=True,exist_ok=True);s=(R/'data/decks'/(c['case']+'.fds')).read_text().replace('T_END=180','T_END=.1').replace('DT_PART=2.','DT_PART=.05');(f/'check.fds').write_text(s);env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0');p=subprocess.run([str(B),'check.fds'],cwd=f,env=env,capture_output=True,text=True,timeout=90);(f/'run.log').write_text(p.stdout+p.stderr);assert p.returncode==0 and 'completed successfully' in (f/(c['case']+'.out')).read_text().lower();ps=first(f/(c['case']+'_1.prt5'));checks=[]
  for k,fuel in enumerate(fuels):
   ex=[p for p in templates[c['geometry_key']]['A']['particles'] if p['fuel']==fuel];xyz=np.array([p['xyz'] for p in ex])+[8,8,0];w=np.array([p['weight'] for p in ex]);x,q=ps[k];dist,ix=cKDTree(x).query(xyz);assert len(x)==400 and len(set(ix))==400 and dist.max()<1e-5;assert np.max(abs(q[ix,2]/w-1))<2e-6;actual=float((q[:,1]*q[:,2]).sum());expected=float(w.sum()*dry[k]*(1+c['moisture']));err=abs(actual/expected-1);assert err<1e-5,(c['case'],fuel,actual,expected,err);checks.append(dict(fuel=fuel,max_position_error_m=float(dist.max()),wet_mass_kg=actual,expected_wet_mass_kg=expected,dry_mass_kg=actual/(1+c['moisture'])))
  rows.append(dict(case=c['case'],seed=c['seed'],moisture=c['moisture'],crown_height_m=c['crown_height_m'],passed=True,checks=checks))
 (R/'results/preflight.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),checks=rows,scope='0.1s input and initial mass checks; not fire behavior, convergence or stochastic outcome validation'),indent=2));print('Passed',len(rows),'native input checks including a different-seed identical-geometry pair')
if __name__=='__main__':main()
