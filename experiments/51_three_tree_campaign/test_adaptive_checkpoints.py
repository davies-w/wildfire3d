import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import worker as w
from checkpoint_control import CheckpointControl,RUN_ID
from build_controller import build
class AdaptiveTests(unittest.TestCase):
 def test_live_segment_change(self):
  clock=[0.];requested=[None]
  def read(seconds):
   return dict(run_id=RUN_ID,checkpoint_seconds=seconds) if seconds==480 or (seconds==180 and clock[0]>=200) else None
  control=CheckpointControl(read,lambda:clock[0]);control.preflight()
  with tempfile.TemporaryDirectory() as td:
   folder=Path(td)
   class Process:
    pid=123;returncode=None
    def poll(self):
     if (folder/'case.stop').exists():requested[0]=clock[0];self.returncode=0
     return self.returncode
   def sleep(n):clock[0]+=1
   with patch.object(w.subprocess,'Popen',return_value=Process()),patch.object(w.time,'monotonic',side_effect=lambda:clock[0]),patch.object(w.time,'sleep',side_effect=sleep):
    r=w.run('fake',folder,480,'case',hard_deadline=2000,checkpoint_control=control)
   self.assertGreaterEqual(requested[0],200);self.assertLess(requested[0],235);self.assertFalse(r['forced_termination'])
 def test_monotonic_policy(self):
  clock=[0];objects={480:dict(run_id=RUN_ID,checkpoint_seconds=480)}
  c=CheckpointControl(objects.get,lambda:clock[0]);c.preflight();self.assertEqual(c.interval(),480)
  objects[300]=dict(run_id=RUN_ID,checkpoint_seconds=300);clock[0]=31;self.assertEqual(c.interval(),300)
  del objects[300];clock[0]=62;self.assertEqual(c.interval(),300)
 def test_failure_safe(self):
  def bad(_):raise OSError('network')
  c=CheckpointControl(bad)
  with self.assertRaises(OSError):c.preflight()
  self.assertEqual(c.interval(),480)
 def test_workflow_thresholds(self):
  steps=build()['adapt_checkpoints']['steps'];choices=next(x['choose']['switch'] for x in steps if 'choose' in x)
  def choose(started,evicted,previous=480):
   seconds=previous
   for rule in choices:
    if eval(rule['condition'][2:-1],{'__builtins__':{}},locals()):return rule['assign'][0]['seconds']
   return seconds
  for a,b,p,result in [(18,1,480,480),(40,2,480,300),(41,2,480,480),(40,4,480,180),(100,4,480,480),(18,0,180,180)]:self.assertEqual(choose(a,b,p),result)
  tasksteps=next(x['count_tasks']['for']['steps'] for x in steps if 'count_tasks' in x)
  flag=next(x['events']['for']['steps'][0]['confirmed']['switch'][0] for x in tasksteps if 'events' in x)
  self.assertIn('50001',flag['condition']);self.assertEqual(flag['assign'],[{'preempted':True}])
if __name__=='__main__':unittest.main()
