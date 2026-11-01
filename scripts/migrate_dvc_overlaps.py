from pathlib import Path
import sys,json,yaml,os,collections
sys.path.insert(0,str(Path.cwd()/'scripts'));import dvc_hf as h
R=h.ROOT; ds=h.definitions(); fixes=[]
# Split only ancestor outputs; most-specific stages retain ownership.
for d in ds:
 root=d['target']; children=[x['target'] for x in ds if x['target']!=root and x['target'].is_relative_to(root)]
 if not children:continue
 if not root.is_dir():raise RuntimeError('Cannot split absent overlapping directory '+str(root))
 parts=[]
 def partition(p):
  if p in children:return
  if any(c.is_relative_to(p) for c in children):
   for f in sorted(p.iterdir()):partition(f)
  else:parts.append(p)
 partition(root)
 fixes.append((d,parts))
print('Splitting',len(fixes),'overlapping ancestor outputs',flush=True)
plan=json.loads((h.STATE/'plan.json').read_text());h.objects.update(plan['objects']);excluded=plan['excluded']
for d,parts in fixes:
 yp=d['yaml'];doc=yaml.safe_load(yp.read_text());definition=doc['stages'][d['stage']];base=yp.parent/definition.get('wdir','.')
 new=[];records=[]
 for p in parts:
  path=os.path.relpath(p,base)
  if p.is_dir():
   entries=[];size=0
   for f in sorted(p.rglob('*')):
    if not f.is_file():continue
    reason=h.approve(f)
    if reason:excluded.append(dict(path=str(f.relative_to(R)),reason=reason));continue
    entries.append(dict(md5=h.register(f),relpath=f.relative_to(p).as_posix()));size+=f.stat().st_size
   if not entries:continue
   rec=dict(path=path,hash='md5',md5=h.directory(entries),size=size,nfiles=len(entries))
  else:
   reason=h.approve(p)
   if reason:excluded.append(dict(path=str(p.relative_to(R)),reason=reason));continue
   rec=h.record_file(p,path)
  new.append(path);records.append(rec)
 values=definition[d['kind']];idx=values.index(d['value']);values[idx:idx+1]=new
 yp.write_text(yaml.safe_dump(doc,sort_keys=False))
 lp=d['lockpath'];lock=yaml.safe_load(lp.read_text());stage=lock['stages'][d['stage']];stage['outs']=[x for x in stage.get('outs',[]) if x['path']!=d['path']]+records;lp.write_text(yaml.safe_dump(lock,sort_keys=False))
 print(d['stage'],d['path'],'->',len(records),'non-overlapping outputs',flush=True)
plan['objects']=h.objects;plan['overlap_repairs']=[dict(stage=d['stage'],path=d['path'],replacement_count=len(parts)) for d,parts in fixes];plan['excluded']=excluded
(h.STATE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
