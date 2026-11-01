"""Verify this migration using normal DVC pull in a fresh Git checkout.
The destination is supplied explicitly; existing source artifacts are never changed.
"""
from pathlib import Path
import argparse,json,subprocess,yaml,hashlib,os,time
import dvc_hf as h
parser=argparse.ArgumentParser();parser.add_argument('checkout',type=Path);a=parser.parse_args();checkout=a.checkout.absolute()
assert checkout.is_relative_to(h.ROOT/'.artifact-staging') and (checkout/'.git').exists()
plan=json.loads((h.STATE/'audit-adoption-plan.json').read_text());targets=[];expected={}
records=subprocess.check_output(['git','ls-files','-z'],cwd=checkout).decode().split('\0')
for name in records:
 if not name.endswith('historical-files.dvc'):continue
 targets.append(name);p=checkout/name
 for item in yaml.safe_load(p.read_text())['outs']:
  assert not item['md5'].endswith('.dir')
  expected[str((p.parent/item['path']).relative_to(checkout))]=item['md5']
# Include every updated pipeline output whose exact object was in this upload.
for d in h.definitions():
 if isinstance(d['value'],dict) and (d['value'][d['path']] or {}).get('cache') is False:continue
 for item in d['lock'].get('stages',{}).get(d['stage'],{}).get('outs',[]):
  if item['path']!=d['path'] or item.get('md5') not in plan['objects']:continue
  target=d['target'].relative_to(h.ROOT).as_posix();targets.append(target);md=item['md5']
  if md.endswith('.dir'):
   data=(h.ROOT/plan['objects'][md]['source']).read_bytes();assert hashlib.md5(data).hexdigest()==md[:-4]
   for entry in json.loads(data):expected[target+'/'+entry['relpath']]=entry['md5']
  else:expected[target]=md
before=subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()
dvc=str(h.ROOT/'.venv/bin/dvc');subprocess.run([dvc,'config','--local','cache.type','hardlink,copy'],cwd=checkout,check=True)
print('Restoring',len(expected),'files through',len(set(targets)),'DVC targets from commit',before,flush=True)
subprocess.run([dvc,'pull',*sorted(set(targets)),'-j','16'],cwd=checkout,check=True)
for i,(name,md) in enumerate(sorted(expected.items())):
 p=checkout/name;assert p.is_file(),name;assert h.digest(p)[0]==md,name
 if i%5000==0:print('Independently MD5-checked',i,'/',len(expected),flush=True)
proof=dict(passed=True,git_commit=before,restored_files=len(expected),targets=len(set(targets)),normal_dvc_pull=True,independent_md5=True,source='Fresh shallow clone from GitHub; artifact bytes from configured public HF HTTP remote',scope='Historical pointers and pipeline objects covered by the migration upload; not all earlier DVC revisions')
(h.STATE/'fresh-checkout-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2),flush=True)
