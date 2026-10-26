"""Replay archived old cases through the new extractor, without simulation or fitting."""
from pathlib import Path
import hashlib,json,tarfile
import numpy as np
from extract_states import extract
R=Path(__file__).resolve().parent;E=R.parent;old=E/'35_surrogate_diagnostics'
def main():
 items=json.loads((old/'attempt12/inventory.json').read_text());base=np.load(old/'attempt20/data/sequences.npz');root=R/'data/extraction-replay';root.mkdir(exist_ok=True);reports=[]
 for i in [0,100,400]:
  it=items[i];c=it['conditions'];n=c['case'];archive=E/it['archive']
  with archive.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
  assert sha==it['expected_sha256'];folder=root/n;folder.mkdir(exist_ok=True);members={};retained=[]
  with tarfile.open(archive) as tar:
   for m in tar:
    name=Path(m.name).name
    if not m.isfile():continue
    if name.endswith(('.prt5','.csv','.fds')) or (name.endswith('.sf') and not any(x.endswith('.sf') for x in retained)):
     b=tar.extractfile(m).read();members[name]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};(folder/name).write_bytes(b);retained.append(name)
  (folder/'verified.json').write_text(json.dumps({'raw_sha256':sha,'members':members,'retained_material_inputs':retained},indent=2)+'\n')
  t,x,audit=extract(folder,c);x=x.astype('float32');t=t.astype('float32');assert np.array_equal(t,base['time'][i])
  delta=np.abs(x-base['state'][i]);np.testing.assert_allclose(x,base['state'][i],rtol=2e-6,atol=2e-5)
  reports.append({'case':n,'index':i,'raw_sha256':sha,'bitwise_state_match':bool(np.array_equal(x,base['state'][i])),'max_abs_difference_by_state':delta.max(0).tolist(),'timestamps_bitwise_match':True})
 result={'passed':True,'cases':reports,'reference':'attempt20/data/sequences.npz','states':['water_kg','dry_fuel_kg','gas_release_kg_s','surface_heating_K'],'training':False,'scope':'Three archived old histories replayed against frozen prior four-state arrays; does not establish model accuracy.'}
 (R/'results/extraction-replay.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
