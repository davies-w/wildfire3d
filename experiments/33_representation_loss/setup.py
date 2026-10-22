from pathlib import Path
import json,shutil,hashlib,numpy as np
R=Path(__file__).parent;S=R.parent/'32_tree_expansion'
def main():
 cs=json.loads((S/'development.json').read_text());scores=json.loads((S/'results/learning.json').read_text())['rows'];heat={x['case']:x['post_source']['truth_mean_HRR_kW'] for x in scores if x['model']=='snapshot'}
 selected=[]
 for split,count in [('train',3),('validation',2)]:
  for height in [4,6,8,10]:
   pool=sorted([c for c in cs if c['new_geometry'] and c['split']==split and c['crown_height_m']==height and c['replica']==0],key=lambda c:(heat[c['case']],c['case']))
   for f in ([0,.5,1] if count==3 else [.25,.75]):selected.append(pool[round(f*(len(pool)-1))])
 assert len(selected)==20 and len({c['configuration'] for c in selected})==20
 (R/'cases.json').write_text(json.dumps(selected,indent=2));names={c['case'] for c in selected};groups=json.loads((S/'groups.json').read_text());(R/'groups.json').write_text(json.dumps([g for g in groups if names.intersection(g['cases'])],indent=2))
 z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in names})
 for n in ['original_cnn.py','geometry_model.py','previous_loss.py','snapshot_evaluation.py','fields.py','fortran_records.py','material_reader.py','preprocess_cloud.py']:shutil.copy2(S/n,R/n)
 shutil.copy2(S/'data/models/geometry_snapshot.pt',R/'data/initial_snapshot.pt')
 (R/'results/selection.json').write_text(json.dumps(dict(training=12,validation=8,rule='Per height: train minimum/median/maximum post-source FDS heat; validation quartiles. Development data only. Deliberately stratified capacity diagnostic, not IID performance estimate.',cases=[dict(case=c['case'],split=c['split'],height=c['crown_height_m'],moisture=c['moisture'],wind=c['wind_speed'],heat_kW=heat[c['case']]) for c in selected]),indent=2))
 (R/'results/source-provenance.json').write_text(json.dumps({n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['original_cnn.py','geometry_model.py','previous_loss.py','snapshot_evaluation.py','fields.py','fortran_records.py','material_reader.py','preprocess_cloud.py','data/initial_snapshot.pt']},indent=2))
if __name__=='__main__':main()
