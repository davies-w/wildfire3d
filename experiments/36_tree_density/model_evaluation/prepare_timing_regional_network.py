"""Prepare one isolated regional subnet; no VM, GPU, job, firewall or training changes."""
from pathlib import Path
import sys,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import gc,save
NAME='fds-timing-east4';REGION='us-east4';CIDR='10.43.0.0/24'
network=gc('compute','networks','describe','fds-trial');assert network['name']=='fds-trial' and network.get('autoCreateSubnetworks') is False
all_subnets=gc('compute','networks','subnets','list','--filter=network:fds-trial')
existing=[s for s in all_subnets if s['name']==NAME and s['region'].endswith('/'+REGION)]
assert len(existing)<=1
created=False
if not existing:
 import ipaddress
 requested=ipaddress.ip_network(CIDR)
 assert all(not requested.overlaps(ipaddress.ip_network(s['ipCidrRange'])) for s in all_subnets)
 gc('compute','networks','subnets','create',NAME,'--network=fds-trial','--region='+REGION,'--range='+CIDR,'--enable-private-ip-google-access');created=True
s=gc('compute','networks','subnets','describe',NAME,'--region='+REGION)
assert s['network'].endswith('/networks/fds-trial') and s['ipCidrRange']==CIDR and s['privateIpGoogleAccess'] is True
save('results/timing-regional-network-prepared.json',dict(passed=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),created_this_invocation=created,subnet=s,scope='One regional subnet in existing isolated fds-trial network. No VM/GPU/job/firewall changes. Quota and subnet are not capacity evidence.'))
print('Verified isolated east4 subnet; no compute resources started')
