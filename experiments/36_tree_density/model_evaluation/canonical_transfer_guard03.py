"""Conservative transfer bound from preserved metadata; no cloud action or billing mutation."""
from pathlib import Path
import datetime,hashlib,json
R=Path(__file__).resolve().parents[1]
def check_transfer_bound(input_bytes,output_bytes,current_prefix='density36/canonical-pilot03/'):
 assert 0<=input_bytes<=2*1024**3 and 0<=output_bytes<=2*1024**3
 objects={};sources={}
 def add(o):
  if isinstance(o,dict) and o.get('bucket')=='tmrw-wildfire-20261015-trial' and o.get('name','').startswith('density36/') and not o['name'].startswith(current_prefix) and 'size' in o:objects[(o['bucket'],o['name'],str(o.get('generation','')))]=int(o['size'])
 for path in sorted((R/'results').glob('*-upload.json')):
  m=json.loads(path.read_text());name=m.get('name','')
  if m.get('bucket')=='tmrw-wildfire-20261015-trial' and name.startswith('density36/') and not name.split('/')[1].startswith('x36-'):
   add(m);sources[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
 for path in sorted((R/'results').glob('*-output-inventory.json')):
  m=json.loads(path.read_text())
  if not isinstance(m.get('objects'),dict):continue
  for o in m['objects'].values():add(o)
  sources[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
 historical=148500758857+1635548567+int(2.25*1024**3);recorded=sum(objects.values());projected=historical+recorded+input_bytes+output_bytes;assert projected<=160*1024**3
 return dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),historical_conservative_bytes=historical,additional_recorded_model_objects=len(objects),additional_recorded_model_bytes=recorded,current_prefix=current_prefix,input_bytes=input_bytes,output_bytes_bound=output_bytes,projected_bytes=projected,limit_bytes=160*1024**3,metadata_source_sha256=sources,scope='Conservative transfer check: retains previous historical total and2.25GiB allowance, adds all distinct preserved model upload/download objects (some overlap is deliberately counted again), then this input/output once. Current prefix excluded from the historical object sum. This is not billing; no shared charge is assumed zero.')
if __name__=='__main__':
 p=json.loads((R/'results/canonical-pilot03-prepared.json').read_text());proof=check_transfer_bound(p['input_bytes'],2*1024**3);(R/'results/canonical-pilot03-transfer-bound.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='metadata_source_sha256'},indent=2))
