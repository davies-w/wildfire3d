"""Actual saved-log regression and negative checks; never runs FDS."""
import unittest,tempfile,json
from pathlib import Path
from completion_check03 import terminal_success
R=Path(__file__).resolve().parent
class Terminal(unittest.TestCase):
 def setUp(self):
  self.root=R/'private02/failure-inspection/evidence';self.result=json.loads((self.root/'result.json').read_text());self.segment=self.result['segments'][0];self.log=self.root/'solve'/self.segment['log']
 def test_actual_normal_completion(self):
  startup=json.loads((self.root/'startup.json').read_text());segment=startup['initial']
  self.assertTrue(terminal_success(segment,.1,self.root/'probe'/segment['log'],target=.1))
 def test_actual_clean_stop_at_end(self):self.assertTrue(terminal_success(self.segment,180.,self.log))
 def test_actual_rejected_restart_never_passes(self):
  s=self.result['segments'][1];self.assertFalse(terminal_success(s,180.,self.root/'solve'/s['log']))
 def test_incomplete_devices_rejected(self):self.assertFalse(terminal_success(self.segment,179.,self.log))
 def test_forced_stop_rejected(self):self.assertFalse(terminal_success(dict(self.segment,forced_termination=True),180.,self.log))
 def test_nonzero_rejected(self):self.assertFalse(terminal_success(dict(self.segment,returncode=1),180.,self.log))
 def test_missing_terminal_marker_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'log';p.write_text(self.log.read_text().replace('STOP: FDS stopped by user',''))
   self.assertFalse(terminal_success(self.segment,180.,p))
 def test_stale_device_end_cannot_override_earlier_log(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'log';p.write_text(self.log.read_text().replace('180.00000 s','179.99000 s'))
   self.assertFalse(terminal_success(self.segment,180.,p))
if __name__=='__main__':unittest.main()
