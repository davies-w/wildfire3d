"""Restore exact selected conifer inputs from existing DVC hashes; no rehash/adoption."""
from pathlib import Path
import json,sys,yaml,hashlib,requests
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
DEST=ROOT/'.artifact-staging/conifer-input-roundtrip'
def main():
 hf.STATE=R/'private07/conifer-input-preservation';hf.STATE.mkdir(exist_ok=True)
 if (hf.STATE/'roundtrip.json').exists():assert json.loads((hf.STATE/'roundtrip.json').read_text())['passed'];return
 lock=yaml.safe_load((R/'dvc.lock').read_text());outs=[o for v in lock['stages'].values() for o in v.get('outs',[])];records=[];expected={}
 for s in json.loads((R/'conifer-cone-selection.json').read_text())['cases']:
  c=s['case'];files=[s['proof']]+[s['solve']+'/'+n for n in ['input.fds',c+'_1.prt5',c+'_hrr.csv',c+'_devc.csv',c+'_1_1.sf',c+'.smv']]
  proof=json.loads((R/s['proof']).read_text())
  for name in files:
   owner=max((o for o in outs if name.startswith(o['path']+'/')),key=lambda o:len(o['path']));h=owner['md5'];assert h.endswith('.dir');cache=hf.STATE/(h+'.json')
   if not cache.exists():
    resp=requests.get('https://huggingface.co/buckets/wdavies/dvc_storage/resolve/wildfire3d/files/md5/'+h[:2]+'/'+h[2:],timeout=90);resp.raise_for_status();assert hashlib.md5(resp.content).hexdigest()==h[:-4];cache.write_bytes(resp.content)
   assert hashlib.md5(cache.read_bytes()).hexdigest()==h[:-4];entry=next(x for x in json.loads(cache.read_text()) if x['relpath']==name[len(owner['path'])+1:]);records.append({'path':str(R/name),'md5':entry['md5'],'hash':'md5'})
   if name!=s['proof']:expected[name]=next(x['sha256'] for x in proof['files'] if x['path']=='solve/'+Path(name).name)
 pointer=hf.STATE/'selected-inputs.dvc';pointer.write_text(yaml.safe_dump({'outs':records}));hf.restore_records([str(pointer)],DEST)
 for name,h in expected.items():assert hf.digest(DEST/R.relative_to(ROOT)/name)[1]==h
 (hf.STATE/'roundtrip.json').write_text(json.dumps({'passed':True,'files':len(records),'raw_inputs_sha256':expected,'source':'Existing frozen completed-output DVC directory manifests; independently restored HF bytes matched retained completion proofs'},indent=2)+'\n');print('PASS conifer raw inputs restored and SHA256 checked',flush=True)
if __name__=='__main__':main()
