from pathlib import Path
import json,hashlib,yaml,shutil
root=Path('/Users/wdavies/pi/wildfire3d');a=root/'experiments/35_surrogate_diagnostics/attempt03';cs=json.loads((a/'cases.json').read_text());groups=json.loads((a/'groups.json').read_text());manifest={};restore=[]
for c in cs:
 n=c['case'];g=next(g['id'] for g in groups if n in g['cases']);base=root/'experiments/32_tree_expansion/data/cloud_archive'/g;meta=json.loads((base/(n+'.summary.json')).read_text());assert hashlib.sha256((base/(n+'.tar.gz')).read_bytes()).hexdigest()==meta['raw_sha256'];manifest[n]='diagnostics35/attempt03/restored/'+n
 for ext in ['.tar.gz','.summary.json']:
  p=base/(n+ext);restore.append(dict(archive_relative=g+'/'+n+ext,target=manifest[n]+ext,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
(a/'input-sources.json').write_text(json.dumps(manifest,indent=2));(a/'restore-manifest.json').write_text(json.dumps(restore,indent=2))
p=a/'launch.py';s=p.read_text().replace('import time,fcntl,hashlib,datetime,subprocess,yaml','import time,fcntl,hashlib,datetime,subprocess,yaml,sys,concurrent.futures');start=s.index("  ledger=read('budget.json')");end=s.index('  # Restore',start);s=s[:start]+'''  ledger=read('budget.json')
  if 'diag35-03' in ledger['reservations']:
   assert '--recover-reserved-setup' in sys.argv
   assert ledger['reservations']['diag35-03']['state']=='reserved_before_upload'
   assert not (R/'results/execution.json').exists()
   assert not gc('workflows','list','--location=us-central1','--filter=name:fds-gpu35-diag03')
  else:
   assert ledger['reserved_usd']+4.5<=ledger['authorized_usd'];ledger['reserved_usd']=round(ledger['reserved_usd']+4.5,2);ledger['reservations']['diag35-03']=dict(state='reserved_before_upload',allowance_usd=4.5,reserved_unix=time.time(),compute_allowance_usd=1.6,ancillary_cleanup_allowance_usd=2.9);save('budget.json',ledger)
'''+s[end:];start=s.index("  for item in read('restore-manifest.json'):");end=s.index('  listings=',start);s=s[:start]+'''  def restore(item):
   source=R.parent.parent/'32_tree_expansion/data/cloud_archive'/item['archive_relative'];assert source.stat().st_size==item['bytes'];assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
   subprocess.run([G,'storage','cp','--if-generation-match=0',str(source),'gs://'+BUCKET+'/'+item['target']],check=True,capture_output=True)
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(restore,read('restore-manifest.json')))
'''+s[end:];s=s.replace("'gs://'+BUCKET+'/expansion32/','gs://'+BUCKET+'/diagnostics35/attempt02/restored/'", "'gs://'+BUCKET+'/diagnostics35/attempt03/restored/'")
start=s.index("  clauses=");end=s.index("  subprocess.run([G,'storage','buckets','add-iam",start);s=s[:start]+'''  assert all(v.startswith('diagnostics35/attempt03/restored/') for v in read('input-sources.json').values())
  clauses=['resource.name.startsWith('+json.dumps(base+'diagnostics35/attempt03/restored/')+')','resource.name == '+json.dumps(base+'diagnostics35/attempt03/pilot-overlay.tar')]
  condition=dict(title='exp35-diag03-fresh-inputs',description='24h fresh verified development48cases only; no old expiring prefixes',expression="request.time < timestamp('"+expiry+"') && ("+' || '.join(clauses)+')');save('results/input-read-condition.json',condition)
'''+s[end:];p.write_text(s)
p=a/'dvc.yaml';d=yaml.safe_load(p.read_text());d['stages']['recover_submission']=dict(d['stages']['cloud_submit']);d['stages']['recover_submission']['cmd']='../../../.venv/bin/python launch.py --recover-reserved-setup';d['stages'].pop('cloud_submit');p.write_text(yaml.safe_dump(d,sort_keys=False))
p=a/'README.md';p.write_text(p.read_text()+"\nPre-submission availability check caught further missing originals. Read-only bucket inspection confirms Delete age1 lifecycle rule. No attempt03 workflow existed or compute was submitted. Recovery uses same alreadyreserved4.50 allowance, restoring all48 raw+summary pairs to fresh immutableprefix after localSHA verification;96objects~6GB, narrow24hreadgrantonlynewprefix+overlay. Bucketpolicyunchanged. This avoids ongoing expiration of old inputs.\n")
(a/'results/lifecycle-diagnosis.json').write_text(json.dumps(dict(rule={'action':{'type':'Delete'},'condition':{'age':1}},compute_submitted=False,workflow_existed=False,action='restore all48 verified inputs under newprefix; same reserved setup; bucket lifecycle unchanged',restored_bytes=sum(v['bytes'] for v in restore)),indent=2))
shutil.copy2('/tmp/fix35lifecycle.py',root/'scripts/recover_surrogate35_expiring_inputs.py')
print('Verified archive inputs',len(restore),sum(v['bytes'] for v in restore))
