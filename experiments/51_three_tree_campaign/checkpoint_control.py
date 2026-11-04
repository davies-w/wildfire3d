"""Read immutable workflow-issued interval reductions from the cloud worker."""
import json, time, urllib.error, urllib.parse, urllib.request
RUN_ID='fds-tree51-campaign01'
BUCKET='tmrw-wildfire-20261015-trial'
PREFIX='tree51/campaign01/control/'
class CheckpointControl:
 def __init__(self,read=None,clock=time.monotonic):
  self.seconds=480;self.next_poll=0.;self.clock=clock;self.read=read or self.cloud_read
 def cloud_read(self,seconds):
  req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
  with urllib.request.urlopen(req,timeout=2) as r:token=json.load(r)['access_token']
  url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(PREFIX+str(seconds)+'.json',safe='')+'?alt=media'
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=2) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code==404:return None
   raise
 def validate(self,d,seconds):
  assert d['run_id']==RUN_ID and d['checkpoint_seconds']==seconds,'Invalid workflow checkpoint control'
 def preflight(self):
  d=self.read(480);assert d is not None,'Workflow control/read grant must exist before solve'
  self.validate(d,480)
 def interval(self):
  if self.clock()<self.next_poll:return self.seconds
  self.next_poll=self.clock()+30
  try:
   for seconds in [180,300]:
    if seconds>=self.seconds:continue
    d=self.read(seconds)
    if d is not None:self.validate(d,seconds);self.seconds=seconds;break
  except (OSError,ValueError,KeyError,AssertionError):
   # Preserve the last verified policy on a read failure; only confirmed evictions shorten it.
   self.last_read_failed=True
  return self.seconds
