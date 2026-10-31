"""Compute local Xet hashes while the scoped bucket upload runs."""
from pathlib import Path
import sys,json,hf_xet
stage=Path(sys.argv[1]);out=Path(sys.argv[2]);paths=sorted(p for p in (stage/'files/md5').rglob('*') if p.is_file());rows={}
for i in range(0,len(paths),1000):
 batch=paths[i:i+1000]
 for p,h in zip(batch,hf_xet.hash_files([str(p) for p in batch])):
  rows['wildfire3d/'+str(p.relative_to(stage))]={'size':h.file_size,'hash':h.hash}
 print('Local content hashes',len(rows),'/',len(paths),flush=True)
out.write_text(json.dumps({'staging':str(stage),'objects':rows}));print(out,flush=True)
