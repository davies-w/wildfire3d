"""Attach-only supervisor: no Batch creation, no new workers or replayed cases."""
from cloud48_05 import *
import yaml,copy,datetime
assert not (P/'supervisor-intent.json').exists()
s=json.loads((P/'status.json').read_text());assert s['controller']['state']=='FAILED'
assert 'Memory usage limit exceeded' in s['controller']['error']['context']
assert len(s['jobs'])==1 and s['jobs'][0]['name'].endswith('/fds-tree48-pilot05-bulk')
w=yaml.safe_load((R/'pilot05.yaml').read_text());cs=w['main']['steps'][0]['init']['assign'][0]['candidates'];assert len(cs)==1
for c in cs:c.pop('job')
steps=w['main']['steps'][1]['campaign']['try']['steps'][0]['waves']['for']['steps']
steps[:]=[x for x in steps if not set(x)&{'quota_gate','create'}]
# Preserve original queue deadline; VM ages remain checked against actual creation.
origin=datetime.datetime.fromisoformat(s['controller']['startTime'].replace('Z','+00:00')).timestamp()
for x in steps:
 if 'set_deadline' in x:x['set_deadline']['assign']=[{'deadline':origin+14400}]
# Partial API responses avoid retaining full VM metadata and embedded bootstrap payloads.
def project(x):
 if isinstance(x,list):
  for v in x:project(v)
 elif isinstance(x,dict):
  if x.get('call')=='http.get':
   a=x['args'];u=a['url'];q=a.setdefault('query',{})
   if '/instances' in u:q.update(fields='items(name,selfLink,creationTimestamp,status),nextPageToken',maxResults=500)
   elif '/disks' in u:q.update(fields='items(name,selfLink,users),nextPageToken',maxResults=500)
   elif '/jobs/' in u:q.update(fields='name,status(state,taskGroups,runDuration)')
  for v in x.values():project(v)
project(w)
zsteps=w['inventory']['steps'][1]['zones']['for']['steps']
for label,var in [('append_vms','v'),('append_disks','d')]:
 i=next(i for i,x in enumerate(zsteps) if label in x)
 zsteps.insert(i,{'page_guard_'+var:{'switch':[{'condition':'${map.get('+var+'.body,"nextPageToken") != null}','raise':'Unexpected inventory pagination; refuse partial inventory'}]}})
w.pop('await_quota')
def calls(x):
 if isinstance(x,dict):
  if x.get('call','').startswith('http.'):yield x
  for v in x.values():yield from calls(v)
 elif isinstance(x,list):
  for v in x:yield from calls(v)
assert not any(x['call']=='http.post' and 'batch.googleapis.com' in x['args']['url'] for x in calls(w))
(R/'supervisor05.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
# Exercise identical inventory under cloud identity with all 20 VMs before attaching.
r={'main':{'steps':[{'init':{'assign':[{'c':copy.deepcopy(cs[0])}]}},{'inspect':{'call':'inventory','args':{'c':'${c}'},'result':'inv'}},{'done':{'return':'${inv}'}}]},'inventory':copy.deepcopy(w['inventory'])}
(R/'supervisor-readiness05.yaml').write_text(yaml.safe_dump(r,sort_keys=False))
print('Prepared attach-only supervisor with projected inventory and original deadlines')
