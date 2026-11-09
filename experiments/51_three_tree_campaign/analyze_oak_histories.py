"""Audit fine histories of the nine randomly selected oaks; no new solves."""
from pathlib import Path
import json,csv
import numpy as np
from preview_training import R,table,sha
OUT=R/'data/oak-history-review'
def main():
 OUT.mkdir(exist_ok=True);rows=[];curves=[]
 for entry in json.loads((R/'ten-case-cone-selection.json').read_text())['cases']:
  case=entry['case'];base=R/'data/ten-case-cone-preview'/case/'cone';meta=json.loads((base/'metadata.json').read_text())
  if meta['static_inputs']['tree_family']!='oak-inspired':continue
  folder=next((R/'data/completed07').glob('*/'+case+'/solve'));proof=json.loads((folder.parent/'proof.json').read_text());sources={}
  for suffix in ['_hrr.csv','_devc.csv']:
   p=folder/(case+suffix);sources[p.name]=sha(p);assert sources[p.name]==next(f['sha256'] for f in proof['files'] if f['path']=='solve/'+p.name)
  hk,h=table(folder/(case+'_hrr.csv'));dk,d=table(folder/(case+'_devc.csv'));cols=[i for i,k in enumerate(dk) if k.endswith(' vapor')];assert len(cols)==7 and all('ignitor' not in dk[i] for i in cols)
  t=d[:,0];v=d[:,cols].sum(1);ht=h[:,0];hr=h[:,hk.index('HRR')];a=np.load(base/'training.npz');assert sha(base/'training.npz')==meta['training_npz_sha256'];heat=a['state'][:,3]
  rawm=json.loads((R/'data/ten-case-cone-preview/base-inputs'/case/'metadata.json').read_text());assert rawm['selected_particle_classes']==[dk[i].removesuffix(' vapor') for i in cols]
  expected=np.interp(a['time_s'],t,v);assert np.allclose(expected,a['state'][:,2],rtol=0,atol=1e-12)
  row={'case':case,'active_saved_volumes':int((a['source_spatial_state'][:,0]>0).sum()),'hrr_peak_kw':float(hr.max()),'hrr_peak_time_s':float(ht[hr.argmax()]),'hrr_max_after_36s_kw':float(hr[ht>=36].max()),'hrr_max_after_60s_kw':float(hr[ht>=60].max()),'hrr_at_end_kw':float(hr[-1]),'tree_vapor_peak_kg_s':float(v.max()),'tree_vapor_peak_time_s':float(t[v.argmax()]),'tree_vapor_integral_kg':float(np.trapezoid(v,t)),'tree_vapor_max_after_36s_kg_s':float(v[t>=36].max()),'heating_index_peak_K':float(heat.max()),'heating_index_peak_time_s':float(a['time_s'][heat.argmax()]),'raw_csv_sha256':sources,'training_npz_sha256':sha(base/'training.npz')};rows.append(row)
  curves.append((case,ht,hr,t,v,a['time_s'],heat))
  np.savez_compressed(OUT/(case+'-histories.npz'),hrr_time_s=ht,hrr_kw=hr,device_time_s=t,tree_vapor_kg_s=v,particle_time_s=a['time_s'],heating_index_K=heat)
 report={'passed':True,'rows':rows,'definitions':{'hrr':'Whole-domain heat release in kW, includes imposed contact ignitor; not tree-only combustion.','tree_vapor':'Sum of the seven vegetation/stem vapor devices, excluding ignitor; released combustible fuel is not itself proof that it all burned. Integral is trapezoidal over actual CSV timestamps.','heating':'Original training heating index: sum(particle mass*(particle temperature-20C))/initial wet mass, K; not maximum gas temperature, not energy.','sampling':'HRR/device histories approximately1s; particle heating approximately2s; volumes approximately36s.','limitations':'No reconstruction of unsaved 3D plume shape/peak. Early activity does not establish sustained ignition. No new simulations or label changes.'}}
 (OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');keys=[k for k in rows[0] if k not in ['raw_csv_sha256','training_npz_sha256']]
 with (OUT/'summary.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axs=plt.subplots(3,1,figsize=(11,10),sharex=True)
 for case,ht,hr,t,v,pt,heat in curves:
  label=case.split('_')[1];axs[0].plot(ht,hr,label=label);axs[1].plot(t,v);axs[2].plot(pt,heat)
 for ax in axs:
  ax.axvspan(0,20.1,color='orange',alpha=.12);ax.axvline(36,color='black',linestyle='--',alpha=.5);ax.grid(alpha=.2);ax.set_xlim(0,60)
 axs[0].set_ylim(bottom=0);axs[1].set_ylim(bottom=0);axs[2].set_ylim(0,max(float(v[6][v[5]<=60].max()) for v in curves)*1.1);axs[0].set_yscale('symlog',linthresh=1);axs[1].set_yscale('symlog',linthresh=1e-5);axs[0].set_ylabel('Total HRR (kW)\nincludes ignitor');axs[1].set_ylabel('Tree-only fuel vapor (kg/s)');axs[2].set_ylabel('Heating index (K)');axs[2].set_xlabel('Simulation time (s)');axs[0].legend(ncol=5,fontsize=8);fig.suptitle('Nine oak-inspired cases: fine histories over first60s\nOrange: imposed ignition interval; dashed: first post-initial saved3D volume');fig.tight_layout();fig.savefig(OUT/'early-histories.png',dpi=140);plt.close(fig)
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
