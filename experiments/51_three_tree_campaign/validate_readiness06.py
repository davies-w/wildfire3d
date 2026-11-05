"""Read actual no-solver children and verify deployed sources before admission."""
from cloud06 import *
import yaml
pkg=json.loads((P/'package.json').read_text())
for n,h in pkg['files'].items():assert sha(R/'data/cloud06'/n)==h,n
s=json.loads((P/'readiness-status.json').read_text());assert s['state']=='SUCCEEDED'
children=[]
for n in json.loads(s['result'])['children']:
 parts=n.split('/');v=gc('workflows','executions','describe',parts[-1],'--workflow='+parts[-3],'--location=us-central1');assert v['state']=='SUCCEEDED',v;result=json.loads(v['result']);assert result['passed'] and result['dry_run'];children.append(v)
save('readiness-children.json',children)
for kind in ['case','epoch','parent','check']:
 name=WF+('-'+kind if kind!='parent' else '');a=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(a['sourceContents'])==yaml.safe_load((R/('rolling06-'+kind+'.yaml')).read_text())
save('readiness-proof.json',dict(passed=True,children_verified=3,deployed_sources_equal=True,index_sha256=pkg['index_sha256']))
print('PASS actual three dry-run children and all four deployed sources')
