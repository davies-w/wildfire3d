from pathlib import Path
import sys,json,yaml,os,csv,subprocess
sys.path.insert(0,str(Path.cwd()/'scripts'));import dvc_hf as h
R=h.ROOT;plan=json.loads((h.STATE/'plan.json').read_text());h.objects.update(plan['objects']);defs=h.definitions();processed=set()
extras=[x['path'] for x in plan['excluded'] if x['reason']=='financial text']
rows=list(csv.DictReader((R/'experiments/43_repository_preservation/results/file-tracking-audit/modified-or-unresolved.csv').open()))
for name in extras+[x['path'] for x in rows]:
 p=R/name;reason=h.approve(p)
 if reason:continue
 owners=[d for d in defs if p==d['target'] or p.is_relative_to(d['target'])]
 if owners:
  d=max(owners,key=lambda d:len(str(d['target'])));t=d['target']
  if t in processed:continue
  processed.add(t)
  if t.is_dir():
   entries=[];size=0
   for f in sorted(t.rglob('*')):
    if f.is_file():entries.append(dict(md5=h.register(f),relpath=f.relative_to(t).as_posix()));size+=f.stat().st_size
   rec=dict(path=d['path'],hash='md5',md5=h.directory(entries),size=size,nfiles=len(entries))
  else:rec=h.record_file(t,d['path'])
  yp=d['yaml'];doc=yaml.safe_load(yp.read_text());v=doc['stages'][d['stage']][d['kind']]
  for i,x in enumerate(v):
   if isinstance(x,dict) and d['path'] in x:x[d['path']].pop('cache',None)
  yp.write_text(yaml.safe_dump(doc,sort_keys=False));lp=d['lockpath'];lock=yaml.safe_load(lp.read_text());s=lock['stages'][d['stage']];s['outs']=[x for x in s.get('outs',[]) if x['path']!=d['path']]+[rec];lp.write_text(yaml.safe_dump(lock,sort_keys=False))
 else:
  parts=p.relative_to(R).parts;parent=R.joinpath(*parts[:2]) if parts[0]=='experiments' else R/parts[0];pointer=parent/'historical-files.dvc';doc=yaml.safe_load(pointer.read_text()) if pointer.exists() else {'outs':[]};path=os.path.relpath(p,parent)
  doc['outs']=[x for x in doc['outs'] if x['path']!=path]+[h.record_file(p,path)];pointer.write_text(yaml.safe_dump(doc,sort_keys=False))
 plan['approved_files'].append(name)
plan['excluded']=[x for x in plan['excluded'] if x['path'] not in extras]
# Native Git symlinks preserve the link itself without duplicating target data.
symlinks=[]
for x in plan['excluded']:
 p=R/x['path']
 if p.is_symlink() and p.resolve().is_relative_to(R):symlinks.append(x['path'])
if symlinks:
 records=[]
 for name in symlinks:
  digest=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=R,input=os.fsencode(os.readlink(R/name))).decode().strip()
  records.append(f'120000 {digest}\t{name}'.encode()+b'\0')
 subprocess.run(['git','update-index','-z','--index-info'],cwd=R,input=b''.join(records),check=True)
plan['git_symlinks']=symlinks;plan['excluded']=[x for x in plan['excluded'] if x['path'] not in symlinks]
for pointer in R.glob('**/historical-files.dvc'):
 if '.artifact-staging' in pointer.parts:continue
 doc=yaml.safe_load(pointer.read_text())
 for x in doc['outs']:
  if os.access(pointer.parent/x['path'],os.X_OK):x['isexec']=True
 pointer.write_text(yaml.safe_dump(doc,sort_keys=False))
plan['objects']=h.objects;(h.STATE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Final plan:',len(h.objects),'objects;',len(symlinks),'Git symlinks;',len(plan['excluded']),'exclusions',flush=True)
