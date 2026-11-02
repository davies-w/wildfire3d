"""Pinned ownership grant plus fresh read-only loser resource inventory."""
from pathlib import Path
import json,sys,subprocess,urllib.request,urllib.parse,hashlib,base64
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET
p=json.loads((R/'results02/package.json').read_text());token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=60)
u='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(p['prefix']+'race-winner.json',safe='')
with get(u) as f:m=json.load(f)
with get(u+'?'+urllib.parse.urlencode(dict(alt='media',generation=m['generation']))) as f:b=f.read()
assert int(m['size'])==len(b) and base64.b64encode(hashlib.md5(b).digest()).decode()==m['md5Hash'];grant=json.loads(b);assert grant['losers_cleanup_verified'] and grant['winner'] in ['or','ia','sc'];losers={}
for c in p['candidates']:
 if c['id']==grant['winner']:continue
 losers[c['id']]={k:gc(*v,'--filter=labels.trial_id='+c['label']) for k,v in dict(jobs=('batch','jobs','list','--location='+c['region']),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(losers[c['id']].values())
proof=dict(passed=True,grant=grant,metadata=m,sha256=hashlib.sha256(b).hexdigest(),losers=losers);(R/'results02/race-winner-verified.json').write_text(json.dumps(proof,indent=2)+'\n');print(grant)
