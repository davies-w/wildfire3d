"""User-authorized freeze of cyclic historical stages, retaining original provenance.
Never executes stages. Original definitions and dependency hashes remain in Git.
"""
from pathlib import Path
import json,yaml,networkx as nx
from dvc.repo import Repo
import dvc.repo.graph as graph_module
ROOT=Path(__file__).resolve().parents[1]
old_check=graph_module.check_acyclic;graph_module.check_acyclic=lambda g:None
repo=Repo(str(ROOT));graph=repo.index.graph;graph_module.check_acyclic=old_check
changes=[];documents={};originals={};locks={}
components=[c for c in nx.strongly_connected_components(graph) if len(c)>1 or graph.has_edge(next(iter(c)),next(iter(c)))]
print('Cyclic components:',len(components),'stages:',sum(map(len,components)),flush=True)
for component in components:
 ordered=sorted(component,key=lambda s:(s.path,list(yaml.safe_load(Path(s.path).read_text())['stages']).index(s.name)))
 rank={s:i for i,s in enumerate(ordered)}
 for stage in ordered:
  p=Path(stage.path);doc=documents.setdefault(p,yaml.safe_load(p.read_text()));definition=doc['stages'][stage.name]
  lp=p.with_name('dvc.lock');lock=locks.setdefault(lp,yaml.safe_load(lp.read_text()));saved=lock.get('stages',{}).get(stage.name,{})
  originals[stage.addressing]=dict(definition=json.loads(json.dumps(definition)),lock=json.loads(json.dumps(saved)))
  remove=[]
  for dep in stage.deps:
   target=Path(dep.fs_path)
   for producer in component:
    if rank[producer]<rank[stage]:continue
    if any(target==Path(o.fs_path) or target.is_relative_to(Path(o.fs_path)) or Path(o.fs_path).is_relative_to(target) for o in producer.outs):
     remove.append(dep.def_path);break
  definition['frozen']=True
  if remove:
   definition['deps']=[x for x in definition.get('deps',[]) if x not in remove]
   if 'deps' in saved:saved['deps']=[x for x in saved['deps'] if x['path'] not in remove]
  changes.append(dict(pipeline=str(p.relative_to(ROOT)),stage=stage.name,removed_dependencies=remove))
# Persist the original records before updating active definitions.
out=ROOT/'docs/historical-dvc-dependencies.json'
if changes:
 if out.exists():raise RuntimeError('Historical archive already exists; do not overwrite it')
 out.write_text(json.dumps(dict(reason='User-authorized historical snapshots; cycles removed and affected stages frozen. This is not a claim of replayable historical optimization.',originals=originals,changes=changes),indent=2)+'\n')
 for p,doc in documents.items():p.write_text(yaml.safe_dump(doc,sort_keys=False))
 for p,lock in locks.items():p.write_text(yaml.safe_dump(lock,sort_keys=False))
print('Frozen stages:',len(changes),'removed links:',sum(len(x['removed_dependencies']) for x in changes),flush=True)
