"""Synthetic clock tests: admission preserves the held-out evaluation reserve."""
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from budget_guard import Guard,EpochBudgetStop

def main():
 policy=dict(training_cap_usd=2,test_reserve_usd=1,buffer_usd=1,rate_upper_usd_hour=1,posted_usd=0,project_cap_usd=4,allocation_not_before_unix=1000)
 with tempfile.TemporaryDirectory() as temp:
  p=Path(temp)/'policy.json';p.write_text(json.dumps(policy));g=Guard(p)
  with patch('budget_guard.upload') as upload,patch('budget_guard.time.time',return_value=1001):
   assert g.admit(1,1,1522);assert upload.call_count==1
  with patch('budget_guard.upload'),patch('budget_guard.time.time',return_value=g.train_deadline-100):
   assert not g.admit(2,1,1522)
   try:g.check_training();raise AssertionError('Failed to stop')
   except EpochBudgetStop:pass
   g.begin_test()
  with patch('budget_guard.time.time',return_value=g.total_deadline):
   try:g.begin_test();raise RuntimeError('Expected deadline rejection')
   except AssertionError:pass
 print('PASS synthetic admission, training stop and protected evaluation reserve')
if __name__=='__main__':main()
