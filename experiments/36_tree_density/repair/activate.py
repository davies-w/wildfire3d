"""Preserve original packages/workflows; create approved replacement coverage and new image pins."""
from pathlib import Path
import json,yaml,lzma,hashlib,copy
R=Path(__file__).resolve().parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 assert not (R/'active-groups.json').exists()
 build=json.loads((R/'results/restore-build-status.json').read_text());assert build['status']=='SUCCESS'
 image=build['results']['images'][0];uri=image['name'].split(':')[0]+'@'+image['digest']
 original=json.loads((R/'groups.json').read_text());active=[]
 for old in original:
  g=copy.deepcopy(old);oldname=g['id'];name='x36-coverage-r1' if g['phase']=='coverage' else oldname;g['id']=name
  folder=R/'jobs'/name;folder.mkdir(exist_ok=True);assert not (folder/'execution.json').exists()
  w=yaml.safe_load((R/'jobs'/oldname/'workflow.yaml').read_text());container=w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container'];container['imageUri']=uri
  if name!=oldname:
   payload=json.loads(lzma.decompress((R/'data/packages'/(oldname+'.xz')).read_bytes()));group=json.loads(payload['group.json']);group['id']=name;payload['group.json']=json.dumps(group)
   blob=lzma.compress(json.dumps(payload).encode(),preset=6);p=R/'data/repair-packages'/(name+'.xz');p.parent.mkdir(exist_ok=True);p.write_bytes(blob);g['package_file']=str(p.relative_to(R));g['package_sha256']=sha(blob)
   w=json.loads(json.dumps(w).replace(oldname,name).replace(old['package_sha256'],g['package_sha256']))
  g['workflow_file']='workflow-r1.yaml';p=folder/g['workflow_file'];p.write_text(yaml.safe_dump(w,sort_keys=False));g['workflow_sha256']=sha(p.read_bytes());g['image_uri']=uri
  (folder/'group-r1.json').write_text(json.dumps(g,indent=2)+'\n');active.append(g)
 assert sum(len(g['cases']) for g in active)==1560
 (R/'active-groups.json').write_text(json.dumps(active,indent=2)+'\n')
 (R/'results/repair-activation.json').write_text(json.dumps(dict(image_uri=uri,original_inputs_preserved=True,changed_scientific_decks=0,new_coverage='x36-coverage-r1',groups=131),indent=2)+'\n')
if __name__=='__main__':main()
