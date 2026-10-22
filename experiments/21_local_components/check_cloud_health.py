"""Read-only active-job/CPU health snapshot; never submits or changes cloud resources."""
import datetime,json,subprocess,urllib.parse,urllib.request
from scene import ROOT
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';project='tmrw-wildfire-20261015'
def gc(*args):return json.loads(subprocess.check_output([G,*args,'--project='+project,'--format=json']))
instances=gc('compute','instances','list');jobs=gc('batch','jobs','list','--location=us-central1');token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();end=datetime.datetime.now(datetime.timezone.utc);start=end-datetime.timedelta(minutes=12)
params={'filter':'metric.type="compute.googleapis.com/instance/cpu/utilization" AND resource.type="gce_instance"','interval.startTime':start.isoformat(),'interval.endTime':end.isoformat(),'view':'FULL'}
url='https://monitoring.googleapis.com/v3/projects/'+project+'/timeSeries?'+urllib.parse.urlencode(params)
with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=30) as response:data=json.load(response)
cpu={s['resource']['labels']['instance_id']:[dict(utc=p['interval']['endTime'],utilization=p['value']['doubleValue']) for p in s.get('points',[])[:3]] for s in data.get('timeSeries',[])}
result=dict(checked_utc=end.isoformat(),instances=[dict(name=i['name'],id=i['id'],status=i['status'],trial=i.get('labels',{}).get('trial_id'),recent_cpu=cpu.get(i['id'],[])) for i in instances],jobs=[dict(name=j['name'],status=j['status']) for j in jobs],limit='CPU activity is evidence of computation, not a verified FDS timestep. Worker solver logs are retained in final bundles, not streamed.')
(ROOT/'results/cloud-health-latest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['instances'],indent=2))
