"""One bounded cloud task, evidence uploaded with VM service account identity."""
import json, os, subprocess, sys, tarfile, time, urllib.request
from pathlib import Path

def upload(path,name):
    req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
    token=json.load(urllib.request.urlopen(req,timeout=10))['access_token']
    from urllib.parse import quote
    url='https://storage.googleapis.com/upload/storage/v1/b/'+os.environ['OUTPUT_BUCKET']+'/o?uploadType=media&ifGenerationMatch=0&name='+quote(name,safe='')
    req=urllib.request.Request(url,data=path.read_bytes(),method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/gzip'})
    with urllib.request.urlopen(req,timeout=90) as r: print('uploaded',name,r.status,flush=True)

mode=os.environ.get('TRIAL_MODE','science')
if mode in ['timeout','watchdog']:
    print('CONTROL_PROBE_STARTED '+mode,flush=True)
    time.sleep(1800)
    raise SystemExit('ERROR: control probe was not stopped')
if mode!='science':raise SystemExit('Unknown mode')
code=1
try:
    code=subprocess.call([sys.executable,'study.py','run','--label=cloud','--cases=flow_medium,fire_medium,heat_conduction_a,pine_needles'])
finally:
    Path('/study/data/cloud').mkdir(parents=True,exist_ok=True)
    out=Path('/tmp/evidence.tar.gz')
    with tarfile.open(out,'w:gz') as t:t.add('/study/data/cloud',arcname='cloud')
    if out.stat().st_size>25*1024**2:raise RuntimeError('Output exceeds 25 MiB limit')
    upload(out,os.environ['OUTPUT_PREFIX']+'/evidence.tar.gz')
sys.exit(code)
