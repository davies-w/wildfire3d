"""Private, conservative elapsed-allocation cost admission; test reserve is separate."""
import json,time,math
from pathlib import Path
from runtime import upload
class EpochBudgetStop(Exception):pass
class Guard:
 def __init__(self,path):
  self.p=json.loads(Path(path).read_text());self.observed={}
  assert self.p['training_cap_usd']>0 and self.p['test_reserve_usd']>0
  assert self.p['rate_upper_usd_hour']>0
  assert self.p['posted_usd']+self.p['training_cap_usd']+self.p['test_reserve_usd']+self.p['buffer_usd']<=self.p['project_cap_usd']
  self.start=self.p['allocation_not_before_unix'];self.train_deadline=self.start+self.p['training_cap_usd']/self.p['rate_upper_usd_hour']*3600
  self.total_deadline=self.start+(self.p['training_cap_usd']+self.p['test_reserve_usd'])/self.p['rate_upper_usd_hour']*3600
 def estimate(self,h,n):
  per_batch={1:.007904364,8:.044284684,16:.088342652,32:.173540081,64:.356534535,90:.512171834}
  nominal=2*(math.ceil(n*(91-h)/256)*per_batch[h]+.62)+30
  return max(nominal,2*self.observed.get(h,0)+30)
 def admit(self,epoch,h,n):
  estimate=self.estimate(h,n);now=time.time();ok=now+estimate+120<self.train_deadline
  upload(f'private-cost/admission-{epoch:03}.json',json.dumps(dict(epoch=epoch,admitted=ok,unix=now,allocation_cost_upper_usd=max(0,now-self.start)*self.p['rate_upper_usd_hour']/3600,next_epoch_seconds_upper=estimate,test_reserve_usd=self.p['test_reserve_usd'])).encode())
  return ok
 def check_training(self):
  if time.time()+120>=self.train_deadline:raise EpochBudgetStop()
 def completed(self,epoch,h,seconds):self.observed[h]=max(self.observed.get(h,0),seconds)
 def begin_test(self):
  assert time.time()+120<self.total_deadline,'Final evaluation reserve exhausted; checkpoint retained'
