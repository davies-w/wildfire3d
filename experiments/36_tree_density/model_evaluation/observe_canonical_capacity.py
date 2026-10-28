"""Read US quota and supported exact machine zones; never infer live stock from quota."""
from pathlib import Path
import datetime,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import gc,save
regions=gc('compute','regions','list','--filter=name~^us-');machines=gc('compute','machine-types','list','--filter=name=g2-standard-4 AND zone:us-');networks=gc('compute','networks','subnets','list','--filter=network:fds-trial')
rows=[]
for r in regions:
 q={x['metric']:dict(limit=x['limit'],usage=x['usage']) for x in r['quotas'] if x['metric'] in ['NVIDIA_L4_GPUS','CPUS','SSD_TOTAL_GB','IN_USE_ADDRESSES']}
 zones=sorted(m['zone'].rsplit('/',1)[-1] for m in machines if m['zone'].rsplit('/',1)[-1].startswith(r['name']+'-') and m['accelerators']==[dict(guestAcceleratorCount=1,guestAcceleratorType='nvidia-l4')])
 rows.append(dict(region=r['name'],quotas=q,exact_g2_standard4_l4_zones=zones))
save('results/canonical-us-capacity-options.json',dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),regions=rows,subnets=networks,scope='Read-only quota, machine catalog and network inventory. None proves available GPU stock; no allocation or model selection.'))
for r in rows:print(r)
