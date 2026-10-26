from pathlib import Path
import json,lzma,hashlib,yaml,ast
R=Path(__file__).resolve().parent.parent
original=json.loads((R/'groups.json').read_text());active=json.loads((R/'active-groups.json').read_text());audit=[]
for old,g in zip(original,active):
 assert old['cases']==g['cases']
 op=json.loads(lzma.decompress((R/'data/packages'/(old['id']+'.xz')).read_bytes()));blob=(R/g.get('package_file','data/packages/'+g['id']+'.xz')).read_bytes();p=json.loads(lzma.decompress(blob));assert hashlib.sha256(blob).hexdigest()==g['package_sha256']
 if g['id']!=old['id']:
  group=json.loads(p['group.json']);group['id']=old['id'];p['group.json']=json.dumps(group)
 assert op==p,'Scientific input or worker changed'
 wp=R/'jobs'/g['id']/g['workflow_file'];assert hashlib.sha256(wp.read_bytes()).hexdigest()==g['workflow_sha256'];w=yaml.safe_load(wp.read_text());ow=yaml.safe_load((R/'jobs'/old['id']/'workflow.yaml').read_text());c=w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container'];assert c['imageUri']==g['image_uri'];ast.parse(c['commands'][1]);c['imageUri']=ow['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['imageUri']
 w=json.loads(json.dumps(w).replace(g['id'],old['id']).replace(g['package_sha256'],old['package_sha256']));assert w==ow
 audit.append(g['id'])
assert len(audit)==131
(R/'results/repair-workflow-preflight.json').write_text(json.dumps(dict(passed=True,groups=131,scientific_packages_identical=True,workflow_changes_only_image_and_replacement_identity=True),indent=2)+'\n')
print('PASS: original worker/decks unchanged; only runtime pin and replacement coverage identity changed')
