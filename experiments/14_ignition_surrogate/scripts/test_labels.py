"""Meaningful failure-mode tests for simulation labels."""
import unittest
from benchmark import classify

class Labels(unittest.TestCase):
    def test_truncated_is_not_negative(self):
        self.assertIsNone(classify([{'Time':2,'ignition_wall':20}],0,'completed successfully',30)['ignited'])
    def test_crash_after_heat_is_not_training_label(self):
        self.assertIsNone(classify([{'Time':2,'ignition_wall':400}],-11,'segfault',30)['ignited'])
    def test_complete_negative(self):
        self.assertIs(classify([{'Time':30,'ignition_wall':349}],0,'completed successfully',30)['ignited'],False)
    def test_early_positive(self):
        self.assertEqual(classify([{'Time':2,'ignition_wall':350}],0,'completed successfully',30)['ignition_time_s'],2)
    def test_nan_invalid(self):
        self.assertIsNone(classify([{'Time':30,'ignition_wall':float('nan')}],0,'completed successfully',30)['ignited'])
    def test_control_event_after_last_periodic_sample(self):
        d=classify([{'Time':15.265496,'ignition_wall':349.98575}],0,'completed successfully',30,15.2974)
        self.assertTrue(d['ignited']);self.assertEqual(d['ignition_time_s'],15.2974)
    def test_invalid_event_time(self):
        self.assertIsNone(classify([{'Time':2,'ignition_wall':350}],0,'completed successfully',30,float('nan'))['ignited'])

if __name__=='__main__':unittest.main()
