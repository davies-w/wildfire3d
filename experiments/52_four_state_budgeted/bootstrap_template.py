import pathlib,sys,runpy,urllib.request,urllib.parse,json,tarfile,shutil,hashlib
p=pathlib.Path('/tmp/study');p.mkdir(exist_ok=True)
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(r,timeout=20))['access_token']
u='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote('fourstate52/training01/inputs.tar',safe='')+'?alt=media'
with urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+token}),timeout=180) as src,(p/'transfer.tar').open('wb') as dst:shutil.copyfileobj(src,dst)
assert hashlib.sha256((p/'transfer.tar').read_bytes()).hexdigest()=='__INPUT_SHA256__'
with tarfile.open(p/'transfer.tar') as tar:
 for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in pathlib.Path(m.name).parts and not m.issym() and not m.islnk()
 tar.extractall(p)
for n,h in json.loads((p/'hashes.json').read_text()).items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
(p/'results').mkdir(exist_ok=True);sys.path.insert(0,str(p));
try:
 from runtime import upload,object_metadata,matches
 probe=b'fourstate52-preflight-upload-verification-probe';upload('upload-probe.bin',probe);assert matches(object_metadata('upload-probe.bin'),probe);upload('upload-probe.bin',probe)
 upload('transport-cloud-check.json',json.dumps({'passed':True,'verified_metadata':True,'idempotent_replay':True}).encode())
 import subprocess
 subprocess.run([sys.executable,str(p/'cloud_check.py')],check=True,timeout=900)
 runpy.run_path(str(p/'worker.py'),run_name='__main__')
except BaseException:
 import traceback
 from runtime import upload
 upload('bootstrap-error.txt',traceback.format_exc().encode());raise
