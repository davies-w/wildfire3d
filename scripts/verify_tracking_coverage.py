"""Account for every original audit candidate against current Git/DVC records."""
from pathlib import Path
import csv,json,subprocess,yaml,hashlib,os,collections
import dvc_hf as h
plan=json.loads((h.STATE/'audit-adoption-plan.json').read_text());excluded={x['path']:x['reason'] for x in plan['excluded']}
git={}
for item in subprocess.check_output(['git','ls-tree','-rz','HEAD'],cwd=h.ROOT).split(b'\0'):
 if item:
  info,name=item.split(b'\t',1);git[name.decode()]=info.decode().split()[2]
tracked={}
for name in git:
 if not name.endswith('historical-files.dvc'):continue
 p=h.ROOT/name
 for item in yaml.safe_load(p.read_text())['outs']:tracked[str((p.parent/item['path']).relative_to(h.ROOT))]=item['md5']
for d in h.definitions():
 if isinstance(d['value'],dict) and (d['value'][d['path']] or {}).get('cache') is False:continue
 for item in d['lock'].get('stages',{}).get(d['stage'],{}).get('outs',[]):
  if item['path']!=d['path']:continue
  md=item.get('md5','');target=d['target'].relative_to(h.ROOT).as_posix()
  if md.endswith('.dir'):
   if md not in plan['objects']:continue
   b=(h.ROOT/plan['objects'][md]['source']).read_bytes();assert hashlib.md5(b).hexdigest()==md[:-4]
   for entry in json.loads(b):tracked[target+'/'+entry['relpath']]=entry['md5']
  else:tracked[target]=md
counts=collections.Counter();failures=[]
rows=list(csv.DictReader((h.ROOT/'experiments/43_repository_preservation/results/file-tracking-audit/not-tracked-project-files.csv').open()))
for row in rows:
 name=row['path'];p=h.ROOT/name
 if name in git:
  b=os.fsencode(os.readlink(p)) if p.is_symlink() else p.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==git[name];counts['git_exact']+=1
 elif name in tracked:
  assert h.digest(p)[0]==tracked[name],name;counts['dvc_exact']+=1
 elif name in excluded:counts['excluded:'+excluded[name]]+=1
 else:failures.append(name)
assert not failures,failures
proof=dict(passed=True,audit_candidates=len(rows),counts=dict(counts),unaccounted_files=failures,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=h.ROOT,text=True).strip(),scope='Every original not-tracked-project-files.csv candidate; existing files checked against Git blobs or current cache-enabled DVC output hashes. Exclusions explicit.')
(h.STATE/'coverage-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
