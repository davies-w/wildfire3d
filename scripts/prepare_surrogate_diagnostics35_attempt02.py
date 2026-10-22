from pathlib import Path
import json,shutil,hashlib,yaml
root=Path('/Users/wdavies/pi/wildfire3d');r=root/'experiments/35_surrogate_diagnostics';a=r/'attempt02';a.mkdir();(a/'data/resume').mkdir(parents=True);(a/'results').mkdir()
for p in r.glob('*.py'):
 s=p.read_text().replace('gpu35-diag01','gpu35-diag02').replace('diag35-01','diag35-02').replace('diagnostics35/attempt01','diagnostics35/attempt02')
 if p.name in ['cloud.py','launch.py','collect.py','prepare_pilot.py']:s=s.replace("R.parent/'33_representation_loss", "R.parent.parent/'33_representation_loss").replace("R.parent/'32_tree_expansion", "R.parent.parent/'32_tree_expansion")
 (a/p.name).write_text(s)
for n in ['cases.json','groups.json','coverage-plan.json']:shutil.copy2(r/n,a/n)
shutil.copy2(r/'data/geometries.npz',a/'data/geometries.npz')
missing=json.loads((r/'results/missing-inputs.json').read_text());missingnames={Path(x['key']).name.split('.')[0] for x in missing};cs=json.loads((a/'cases.json').read_text());groups=json.loads((a/'groups.json').read_text());manifest={};restore=[]
for c in cs:
 n=c['case'];g=next(g['id'] for g in groups if n in g['cases']);base=root/'experiments/32_tree_expansion/data/cloud_archive'/g
 meta=json.loads((base/(n+'.summary.json')).read_text())
 if n in missingnames:
  raw=base/(n+'.tar.gz');assert hashlib.sha256(raw.read_bytes()).hexdigest()==meta['raw_sha256']
  for ext in ['.tar.gz','.summary.json']:
   p=base/(n+ext);restore.append(dict(archive_relative=g+'/'+n+ext,target='diagnostics35/attempt02/restored/'+n+ext,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
  manifest[n]='diagnostics35/attempt02/restored/'+n
 else:manifest[n]='expansion32/'+g+'/'+n
(a/'input-sources.json').write_text(json.dumps(manifest,indent=2));(a/'restore-manifest.json').write_text(json.dumps(restore,indent=2))
p=a/'preprocess_cloud.py';s=p.read_text().replace("prefix='expansion32/'+group+'/'+n", "prefix=json.loads((R/'input-sources.json').read_text())[n]");p.write_text(s)
p=a/'prepare_pilot.py';s=p.read_text().replace("R/'coverage-plan.json'", "R/'coverage-plan.json',R/'input-sources.json',R/'restore-manifest.json'");p.write_text(s)
p=a/'launch.py';s=p.read_text();needle="  subprocess.run([G,'storage','cp','--if-generation-match=0',str(R/'data/pilot-overlay.tar')";i=s.index(needle);s=s[:i]+'''  # Restore only verified missing inputs, under a new immutable attempt prefix.
  for item in read('restore-manifest.json'):
   source=R.parent.parent/'32_tree_expansion/data/cloud_archive'/item['archive_relative'];assert source.stat().st_size==item['bytes'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
   subprocess.run([G,'storage','cp','--if-generation-match=0',str(source),'gs://'+BUCKET+'/'+item['target']],check=True)
  listings=subprocess.run([G,'storage','ls','--recursive','gs://'+BUCKET+'/expansion32/','gs://'+BUCKET+'/diagnostics35/attempt02/restored/'],check=True,text=True,capture_output=True).stdout.splitlines();present=set(listings)
  for prefix in read('input-sources.json').values():
   for ext in ['.summary.json','.tar.gz']:assert 'gs://'+BUCKET+'/'+prefix+ext in present,(prefix,ext)
  save('results/input-availability.json',dict(passed=True,objects=2*len(read('input-sources.json')),restored=len(read('restore-manifest.json'))))
'''+s[i:];s=s.replace("clauses=['resource.name == '", "clauses=['resource.name.startsWith('+json.dumps(base+'diagnostics35/attempt02/restored/')+')','resource.name == '");p.write_text(s)
p=a/'collect.py';s=p.read_text().replace("  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt02/error.txt'", "  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt02/bootstrap-error.txt',str(dest)],check=False)\n  subprocess.run([G,'storage','cp','gs://'+BUCKET+'/diagnostics35/attempt02/error.txt'");p.write_text(s)
(a/'restore_inputs.py').write_text("from pathlib import Path\nimport shutil\nR=Path(__file__).parent\n(R/'data').mkdir(exist_ok=True)\nfor n in ['cases.json','groups.json','coverage-plan.json','data/geometries.npz']:shutil.copy2(R.parent/n,R/n)\n")
d=yaml.safe_load((r/'dvc.yaml').read_text());d['stages']['inputs']=dict(cmd='../../../.venv/bin/python restore_inputs.py',deps=['restore_inputs.py','../cases.json','../groups.json','../coverage-plan.json','../data/geometries.npz'],outs=[{'cases.json':{'cache':False}},{'groups.json':{'cache':False}},{'coverage-plan.json':{'cache':False}},'data/geometries.npz'])
for name,st in d['stages'].items():
 if name!='inputs':st['cmd']=st['cmd'].replace('../../.venv','../../../.venv')
 if name=='package':st['deps']=[x.replace('../32_tree_expansion','../../32_tree_expansion') for x in st['deps']]+['input-sources.json','restore-manifest.json']
(a/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False));(a/'README.md').write_text((r/'README.md').read_text()+"\n\nAttempt02: separately reserved4.50 replacement for startup404 in attempt01. Five selected training bundles were absent from GCS but retained locally with matching raw SHA256. Restore only those five bundles plus their metadata under this attempt's own prefix; verify all96 inputobjectpaths exist before submission. No scientific/worker/epoch changes. Attempt01 reservation retained; cumulative79.10/100. Original frozen payload unchanged.\n")
(r/'results/failure-diagnosis.json').write_text(json.dumps(dict(cause='HTTP404 on first preprocessing summary; five selected training bundles missing remotely, verified local originals available',no_training=True,cleanup_verified=True,replacement='attempt02 separately reserved; same science; new input mapping and verified restoration'),indent=2))
p=root/'scripts/prepare_surrogate_diagnostics35_attempt02.py';shutil.copy2('/tmp/prepare35r2.py',p)
