"""Require exact case-level coverage and immutable raw verification before completion."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text())
def main():
 expected={c['case'] for c in read('cases.json')};assert len(expected)==1560
 inventory=read('data/raw-inventory.json');rows={r['case']:r for r in inventory['archives']}
 assert len(rows)==len(inventory['archives'])==1560 and set(rows)==expected
 extraction=read('results/four-state-extraction.json');extracted={c['case']:c for c in extraction['cases']}
 assert extraction['histories']==1560 and not extraction['awaiting_exact_timestamps'] and set(extracted)==expected
 total=0
 for name,row in rows.items():
  proof=read('data/verified-material/'+name+'/verified.json')
  assert proof['case']==name and proof['raw_sha256']==row['sha256']==extracted[name]['raw_sha256']
  assert proof['raw_uri']==row['uri'] and proof['raw_bytes']==row['bytes'] and proof['checkpoint_hashes_verified']
  assert (R/'data/four-state'/(name+'.npz')).is_file()
  total+=proof['raw_bytes']
 recovered=[]
 for group in ['032','088','093','115']:
  root='data/recovery-collected/x36-density-'+group+'-r1/'
  proof=read(root+'verified.json');assert proof['cleanup_verified'] and proof['all_full_horizon']
  assert read(root+'cleanup.json')=={'instances':[],'disks':[],'jobs':[]}
  assert read(root+'job-status.json')['status']['state']=='SUCCEEDED'
  recovered+=proof['cases']
 assert len(recovered)==len(set(recovered))==29
 merged=read('results/learning-data.json');assert merged['histories']==2080 and merged['new_histories']==1560 and merged['configurations']==2040
 assert merged['old_states_times_bitwise_preserved'] and merged['old_activity_labels_exact'] and merged['replicas_grouped']
 assert hashlib.sha256((R/'data/learning/sequences.npz').read_bytes()).hexdigest()==merged['sequences_sha256']
 report={'passed':True,'new_histories':1560,'merged_histories':2080,'unique_configurations':2040,'raw_bytes_verified':total,'raw_sha_and_checkpoint_verification':True,'exact_case_set':True,'recovered_unfinished_cases':29,'old_states_times_bitwise_preserved':True,'training_started':False,'scope':'Dataset completeness and extraction provenance only; no model accuracy or physical validation. Full raw and checkpoint archives retained in private GCS.'}
 (R/'results/dataset-completeness.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
