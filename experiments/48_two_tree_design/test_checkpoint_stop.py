"""Control-flow regression tests with a fake process; never executes FDS."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pilot_worker06 as w
class StopTests(unittest.TestCase):
 def exercise(self,delay,grace,deadline):
  with tempfile.TemporaryDirectory() as td:
   folder=Path(td);clock=[0.];requested=[None];killed=[]
   class Process:
    pid=123;returncode=None
    def poll(self):
     if (folder/'case.stop').exists() and requested[0] is None:requested[0]=clock[0]
     if requested[0] is not None and clock[0]-requested[0]>=delay:self.returncode=0
     return self.returncode
    def wait(self,timeout=None):self.returncode=-15;return -15
   def sleep(n):clock[0]+=10
   with patch.object(w.subprocess,'Popen',return_value=Process()),patch.object(w.time,'monotonic',side_effect=lambda:clock[0]),patch.object(w.time,'sleep',side_effect=sleep),patch.object(w.os,'killpg',side_effect=lambda *a:killed.append(a)):
    result=w.run('fake',folder,5,'case',grace_seconds=grace,hard_deadline=deadline)
   return result,killed
 def test_stop_over_old_90_seconds_finishes_cleanly(self):
  r,k=self.exercise(120,900,1200);self.assertEqual(r['returncode'],0);self.assertFalse(r['forced_termination']);self.assertFalse(k);self.assertGreater(r['stop_wait_seconds'],90)
 def test_absolute_deadline_remains_bounded(self):
  r,k=self.exercise(10000,900,100);self.assertTrue(r['forced_termination']);self.assertTrue(k);self.assertLessEqual(r['wall_seconds'],110)
if __name__=='__main__':unittest.main()
