"""Area-matched face histories and native raw field evidence; no ignition gate."""
import csv,json,hashlib,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).parent

def csvdata(path):
 with path.open() as f:
  r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)];v=np.array([list(map(float,row)) for row in r if row])
 return dict(zip(keys,v.T))
def main():
 cases=json.loads((ROOT/'cases.json').read_text());out=ROOT/'data/analysis';out.mkdir(exist_ok=True);summaries=[];series={}
 for c in cases:
  name=c['case'];folder=ROOT/'data/cloud'/name
  if not (folder/'result.json').exists():continue
  result=json.loads((folder/'result.json').read_text());d=csvdata(folder/(name+'_devc.csv'));t=d['Time'];h=csvdata(folder/(name+'_hrr.csv'))
  row=dict(case=name,layout=c['layout'],dx=c['dx'],expanded=c['expanded'],complete=result['full_horizon'],end_s=float(t[-1]),wall_s=result['wall_seconds'],faces={})
  face_arrays={}
  for face in [-1,1,-2,2,3]:
   pts=[p for p in c['patches'] if p['ior']==face];values=np.array([d[p['id']+'_T'] for p in pts]);coarse={}
   for p in pts:
    coord=p['xyz'];key=tuple(int(np.floor(coord[i])) for i in range(3) if i!=abs(face)-1)
    coarse.setdefault(key,[]).append(p)
   keys=sorted(coarse);q=np.array([np.mean([d[p['id']+'_T'] for p in coarse[k]],axis=0) for k in keys]);flux=np.array([np.mean([d[p['id']+'_R']+d[p['id']+'_C'] for p in coarse[k]],axis=0) for k in keys])
   face_arrays[face]=(keys,q,flux)
   row['faces'][str(face)]=dict(final_mean_C=float(q[:,-1].mean()),final_native_max_C=float(values[:,-1].max()),final_common_patch_max_C=float(q[:,-1].max()),peak_native_C=float(values.max()),mean_incoming_radiation_plus_convection_dose_kJ_m2=float(np.trapezoid(flux,t,axis=1).mean()))
  row['total_released_energy_kJ']=float(np.trapezoid(h['HRR'],h['Time']))
  row['remaining_wet_particle_mass_kg']={str(i):float(sum(v[-1] for k,v in d.items() if k.startswith(f'c{i} mass '))) for i in [0,1]}
  series[name]=(t,face_arrays);summaries.append(row)
  # fds2ascii validates raw boundary temperature evidence over the final available2s.
  bdir=out/name;bdir.mkdir(exist_ok=True)
  for face in [-1,1,-2,2,3]:
   path=bdir/f'raw-temperature-face{face}.csv'
   if not path.exists():
    answer=f'{name}\n3\n1\nn\n{max(0,t[-1]-2)} {t[-1]}\n{face}\n1\n1\n{path.resolve()}\n'
    p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=answer,text=True,capture_output=True,timeout=120)
    path.with_suffix('.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0 and path.exists(),(name,face,p.stdout[-1000:])
  row['raw_evidence_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.suffix in ['.bf','.sf','.prt5']}
 pairs=[]
 for layout in 'ABC':
  subset=[c for c in cases if c['layout']==layout and c['case'] in series]
  for i,a in enumerate(subset):
   for b in subset[i+1:]:
    if a['dx']!=b['dx'] and a['expanded']!=b['expanded']:continue
    ta,fa=series[a['case']];tb,fb=series[b['case']];tt=np.arange(0,min(ta[-1],tb[-1])+1e-6,1)
    record=dict(a=a['case'],b=b['case'],comparison='air_volume' if a['dx']==b['dx'] else 'resolution',common_end_s=float(tt[-1]),faces={})
    for face in fa:
     ka,qa,xa=fa[face];kb,qb,xb=fb[face];assert ka==kb
     aa=np.array([np.interp(tt,ta,x) for x in qa]);bb=np.array([np.interp(tt,tb,x) for x in qb]);diff=aa-bb
     record['faces'][str(face)]=dict(history_MAE_C=float(abs(diff).mean()),history_RMSE_C=float(np.sqrt((diff**2).mean())),final_map_MAE_C=float(abs(diff[:,-1]).mean()),final_map_max_abs_difference_C=float(abs(diff[:,-1]).max()))
    pairs.append(record)
  if subset:
   fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
   for ax,face in zip(axes.flat,[-1,1,-2,2,3]):
    for c in subset:
     t,fa=series[c['case']];q=fa[face][1];label=('expanded' if c['expanded'] else 'compact')+f' / {c["dx"]}m'
     ax.plot(t,q.mean(axis=0),label=label)
    ax.set(title={-1:'West wall',1:'East wall',-2:'South wall',2:'North wall',3:'Roof'}[face],xlabel='Time (s)',ylabel='Area-average surface temperature (°C)');ax.grid(alpha=.2)
   axes.flat[5].axis('off');axes.flat[0].legend(fontsize=8);fig.suptitle(f'Layout {layout}: matched surface-temperature histories');fig.savefig(out/f'layout-{layout}-temperature.png',dpi=150);plt.close(fig)
 report=dict(cases=summaries,pairs=pairs,limitations='Single realizations, generic materials and imposed source. No convergence or physical-validation claim. Radiation+convection dose uses incoming radiation rather than net absorbed energy. Raw boundary csv is final2s average, not instantaneous endpoint. Incomplete horizons compared only over common available time.')
 (ROOT/'results/comparison.json').write_text(json.dumps(report,indent=2));print('Analyzed',len(summaries),'cases and',len(pairs),'matched comparisons')
if __name__=='__main__':main()
