"""Reject unsafe job configurations before they reach the cloud API."""
import copy,unittest
from make_workflow import job

def validate(j):
    groups=j['taskGroups'];assert len(groups)==1
    g=groups[0];assert all(int(g[k])==1 for k in ['taskCount','parallelism','taskCountPerNode'])
    s=g['taskSpec'];assert s['maxRetryCount']==0
    assert 0<int(s['maxRunDuration'].removesuffix('s'))<=600
    assert s['computeResource']=={'cpuMilli':4000,'memoryMib':12000}
    instances=j['allocationPolicy']['instances'];assert len(instances)==1
    policy=instances[0]['policy'];assert policy['machineType']=='c3-standard-4' and policy['provisioningModel']=='SPOT'
    assert not policy.get('accelerators') and int(policy['bootDisk']['sizeGb'])<=30
    assert '@sha256:' in s['runnables'][0]['container']['imageUri']
    assert j['allocationPolicy']['location']['allowedLocations']==['zones/us-central1-a']

class Controls(unittest.TestCase):
    def setUp(self):self.j=job('us-central1-docker.pkg.dev/tmrw-wildfire-20261015/fds/study15@sha256:'+'a'*64,'science')
    def test_valid(self):validate(self.j)
    def test_parallel(self):
        self.j['taskGroups'][0]['parallelism']='2'
        with self.assertRaises(AssertionError):validate(self.j)
    def test_retry(self):
        self.j['taskGroups'][0]['taskSpec']['maxRetryCount']=1
        with self.assertRaises(AssertionError):validate(self.j)
    def test_on_demand(self):
        self.j['allocationPolicy']['instances'][0]['policy']['provisioningModel']='STANDARD'
        with self.assertRaises(AssertionError):validate(self.j)
    def test_timeout(self):
        self.j['taskGroups'][0]['taskSpec']['maxRunDuration']='1801s'
        with self.assertRaises(AssertionError):validate(self.j)
    def test_unpinned(self):
        self.j['taskGroups'][0]['taskSpec']['runnables'][0]['container']['imageUri']='image:latest'
        with self.assertRaises(AssertionError):validate(self.j)

if __name__=='__main__':unittest.main()
